import os
import uuid
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app

from app.core.document_parser import DocumentParser
from app.core.text_splitter import TextSplitter
from app.core.index_manager import IndexManager

api_bp = Blueprint('api', __name__)

_doc_parser = None
_text_splitter = None
_index_manager = None


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
        _index_manager = IndexManager(current_app.config['INDEX_DIR'])
    return _index_manager


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
        else:
            data = request.get_json() or {}
            query = data.get('q', '').strip()
            top_k = int(data.get('top_k', 3))

        if not query:
            return jsonify({
                'success': False,
                'error': 'Query parameter "q" is required'
            }), 400

        top_k = max(1, min(top_k, 20))

        index_mgr = get_index_manager()
        results = index_mgr.search(query, top_k=top_k)

        formatted_results = []
        for result in results:
            formatted_results.append({
                'doc_id': result['doc_id'],
                'chunk_id': result['chunk_id'],
                'filename': result['filename'],
                'section': result['section'],
                'content': result['content'],
                'highlighted': result['highlighted'],
                'score': round(result['score'], 4),
                'start_pos': result['start_pos'],
                'end_pos': result['end_pos'],
                'chunk_index': result['chunk_index'],
                'total_chunks': result['total_chunks'],
                'page': result['page'],
                'matched_keywords': result['matched_keywords']
            })

        return jsonify({
            'success': True,
            'data': {
                'query': query,
                'total': len(formatted_results),
                'top_k': top_k,
                'results': formatted_results
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
