import os
import uuid
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app

from app.core.document_parser import DocumentParser
from app.core.text_splitter import TextSplitter
from app.core.index_manager import IndexManager
from app.core.search_enhancer import SearchEnhancer

api_bp = Blueprint('api', __name__)

_doc_parser = None
_text_splitter = None
_index_manager = None
_search_enhancer = None


def get_doc_parser():
    global _doc_parser
    if _doc_parser is None:
        _doc_parser = DocumentParser()
    return _doc_parser


def get_text_splitter():
    global _text_splitter
    if _text_splitter is None:
        _text_splitter = TextSplitter(chunk_size=512, chunk_overlap=50)
    return _text_splitter


def get_index_manager():
    global _index_manager
    if _index_manager is None:
        data_dir = os.path.join(os.path.dirname(current_app.config['INDEX_DIR']), 'data')
        _index_manager = IndexManager(current_app.config['INDEX_DIR'], data_dir)
    return _index_manager


def get_search_enhancer():
    global _search_enhancer
    if _search_enhancer is None:
        data_dir = os.path.join(os.path.dirname(current_app.config['INDEX_DIR']), 'data')
        _search_enhancer = SearchEnhancer(data_dir)
    return _search_enhancer


@api_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })


@api_bp.route('/stats', methods=['GET'])
def get_stats():
    try:
        index_mgr = get_index_manager()
        stats = index_mgr.get_stats()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/documents', methods=['GET'])
def get_documents():
    try:
        index_mgr = get_index_manager()
        docs = index_mgr.get_all_documents()

        result = []
        for doc in docs:
            upload_time = doc['upload_time']
            if hasattr(upload_time, 'isoformat'):
                upload_time_str = upload_time.isoformat()
            else:
                upload_time_str = str(upload_time)

            result.append({
                'doc_id': doc['doc_id'],
                'filename': doc['filename'],
                'upload_time': upload_time_str,
                'chunk_count': doc['chunk_count']
            })

        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/documents/upload', methods=['POST'])
def upload_document():
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        if not DocumentParser.is_supported(file.filename):
            return jsonify({
                'success': False,
                'error': f'Unsupported file format. Supported formats: PDF, Word, Markdown, TXT'
            }), 400

        doc_id = uuid.uuid4().hex
        ext = os.path.splitext(file.filename)[1].lower()
        saved_filename = f"{doc_id}{ext}"
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], saved_filename)
        file.save(save_path)

        try:
            doc_parser = get_doc_parser()
            parsed = doc_parser.parse(save_path)

            text_splitter = get_text_splitter()
            chunks = text_splitter.split_sections(parsed['sections'])

            if not chunks:
                chunks = text_splitter.split_text(
                    parsed['full_text'],
                    metadata={'section': parsed['filename']}
                )

            index_mgr = get_index_manager()
            added_count = index_mgr.add_document(
                doc_id=doc_id,
                filename=file.filename,
                chunks=chunks,
                upload_time=datetime.now()
            )

            return jsonify({
                'success': True,
                'data': {
                    'doc_id': doc_id,
                    'filename': file.filename,
                    'chunk_count': added_count,
                    'sections_count': len(parsed['sections'])
                }
            })

        except Exception as e:
            if os.path.exists(save_path):
                os.remove(save_path)
            raise e

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/documents/<doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    try:
        index_mgr = get_index_manager()

        if not index_mgr.document_exists(doc_id):
            return jsonify({
                'success': False,
                'error': 'Document not found'
            }), 404

        deleted_count = index_mgr.delete_document(doc_id)

        upload_dir = current_app.config['UPLOAD_FOLDER']
        for filename in os.listdir(upload_dir):
            if filename.startswith(doc_id):
                file_path = os.path.join(upload_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)

        return jsonify({
            'success': True,
            'data': {
                'doc_id': doc_id,
                'deleted_chunks': deleted_count
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/search', methods=['GET', 'POST'])
def search():
    try:
        if request.method == 'GET':
            query = request.args.get('q', '').strip()
            top_k = int(request.args.get('top_k', 3))
            doc_id = request.args.get('doc_id', '').strip() or None
        else:
            data = request.get_json() or {}
            query = data.get('q', '').strip()
            top_k = int(data.get('top_k', 3))
            doc_id = data.get('doc_id', '').strip() or None

        if not query:
            return jsonify({
                'success': False,
                'error': 'Query parameter "q" is required'
            }), 400

        top_k = max(1, min(top_k, 20))

        index_mgr = get_index_manager()
        search_result = index_mgr.search(query, top_k=top_k, doc_id=doc_id)
        
        results = search_result['results']

        formatted_results = []
        for result in results:
            formatted_results.append({
                'doc_id': result['doc_id'],
                'chunk_id': result['chunk_id'],
                'filename': result['filename'],
                'section': result['section'],
                'content': result['content'],
                'focus_content': result['focus_content'],
                'highlighted': result['highlighted'],
                'highlighted_focus': result['highlighted_focus'],
                'score': round(result['score'], 4),
                'base_score': result['base_score'],
                'phrase_boost': result['phrase_boost'],
                'start_pos': result['start_pos'],
                'end_pos': result['end_pos'],
                'chunk_index': result['chunk_index'],
                'total_chunks': result['total_chunks'],
                'page': result['page'],
                'matched_keywords': result['matched_keywords'],
                'focus_matched_keywords': result['focus_matched_keywords']
            })

        return jsonify({
            'success': True,
            'data': {
                'query': query,
                'total': len(formatted_results),
                'top_k': top_k,
                'doc_id': doc_id,
                'results': formatted_results,
                'expanded_keywords': search_result['expanded_keywords'],
                'phrases': search_result['phrases'],
                'corrected_query': search_result['corrected_query'],
                'spell_corrections': search_result['spell_corrections'],
                'similar_queries': search_result['similar_queries']
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/synonyms', methods=['GET'])
def get_synonyms():
    try:
        enhancer = get_search_enhancer()
        synonyms = enhancer.get_all_synonyms()
        return jsonify({
            'success': True,
            'data': synonyms
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/synonyms', methods=['POST'])
def add_synonym():
    try:
        data = request.get_json() or {}
        word = data.get('word', '').strip()
        synonym = data.get('synonym', '').strip()

        if not word or not synonym:
            return jsonify({
                'success': False,
                'error': 'Both "word" and "synonym" are required'
            }), 400

        enhancer = get_search_enhancer()
        enhancer.add_synonym(word, synonym)

        return jsonify({
            'success': True,
            'message': f'Synonym added: {word} -> {synonym}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/synonyms', methods=['DELETE'])
def remove_synonym():
    try:
        data = request.get_json() or {}
        word = data.get('word', '').strip()
        synonym = data.get('synonym', '').strip()

        if not word or not synonym:
            return jsonify({
                'success': False,
                'error': 'Both "word" and "synonym" are required'
            }), 400

        enhancer = get_search_enhancer()
        enhancer.remove_synonym(word, synonym)

        return jsonify({
            'success': True,
            'message': f'Synonym removed: {word} -> {synonym}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/synonyms/batch', methods=['POST'])
def update_synonyms_batch():
    try:
        data = request.get_json() or {}
        synonyms_dict = data.get('synonyms', {})

        if not isinstance(synonyms_dict, dict):
            return jsonify({
                'success': False,
                'error': 'synonyms must be a dictionary'
            }), 400

        enhancer = get_search_enhancer()
        enhancer.update_synonyms_dict(synonyms_dict)

        return jsonify({
            'success': True,
            'message': 'Synonyms dictionary updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/spellcheck', methods=['GET', 'POST'])
def spell_check():
    try:
        if request.method == 'GET':
            query = request.args.get('q', '').strip()
        else:
            data = request.get_json() or {}
            query = data.get('q', '').strip()

        if not query:
            return jsonify({
                'success': False,
                'error': 'Query parameter "q" is required'
            }), 400

        enhancer = get_search_enhancer()
        corrected_query, corrections = enhancer.correct_spelling(query)

        return jsonify({
            'success': True,
            'data': {
                'original_query': query,
                'corrected_query': corrected_query,
                'corrections': corrections
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/similar-queries', methods=['GET', 'POST'])
def similar_queries():
    try:
        if request.method == 'GET':
            query = request.args.get('q', '').strip()
            top_k = int(request.args.get('top_k', 5))
        else:
            data = request.get_json() or {}
            query = data.get('q', '').strip()
            top_k = int(data.get('top_k', 5))

        if not query:
            return jsonify({
                'success': False,
                'error': 'Query parameter "q" is required'
            }), 400

        enhancer = get_search_enhancer()
        similar = enhancer.find_similar_queries(query, top_k=top_k)

        return jsonify({
            'success': True,
            'data': {
                'query': query,
                'similar_queries': similar
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/query-history', methods=['GET'])
def get_query_history():
    try:
        limit = int(request.args.get('limit', 50))
        enhancer = get_search_enhancer()
        history = enhancer.get_query_history(limit=limit)

        return jsonify({
            'success': True,
            'data': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/query-history', methods=['DELETE'])
def clear_query_history():
    try:
        enhancer = get_search_enhancer()
        enhancer.clear_query_history()

        return jsonify({
            'success': True,
            'message': 'Query history cleared'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/query-history/record', methods=['POST'])
def record_query():
    try:
        data = request.get_json() or {}
        query = data.get('q', '').strip()

        if not query:
            return jsonify({
                'success': False,
                'error': 'Query parameter "q" is required'
            }), 400

        enhancer = get_search_enhancer()
        enhancer.record_query(query)

        return jsonify({
            'success': True,
            'message': 'Query recorded'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
