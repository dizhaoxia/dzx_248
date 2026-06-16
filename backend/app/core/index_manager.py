import os
import jieba
import re
import shutil
from typing import List, Dict, Optional
from datetime import datetime

from whoosh.index import create_in, open_dir, exists_in
from whoosh.fields import Schema, TEXT, ID, NUMERIC, DATETIME, STORED, KEYWORD
from whoosh.query import Term, Or
from whoosh import scoring
from whoosh.qparser import QueryParser


class IndexManager:
    def __init__(self, index_dir: str):
        self.index_dir = index_dir
        self.ix = None
        self._init_index()

    def _init_index(self):
        os.makedirs(self.index_dir, exist_ok=True)

        schema = Schema(
            doc_id=ID(stored=True),
            chunk_id=ID(stored=True, unique=True),
            filename=STORED,
            section=STORED,
            content=STORED,
            content_index=TEXT,
            start_pos=NUMERIC(stored=True),
            end_pos=NUMERIC(stored=True),
            chunk_index=NUMERIC(stored=True),
            total_chunks=NUMERIC(stored=True),
            page=NUMERIC(stored=True),
            upload_time=DATETIME(stored=True)
        )

        if exists_in(self.index_dir):
            try:
                self.ix = open_dir(self.index_dir)
            except Exception:
                shutil.rmtree(self.index_dir)
                os.makedirs(self.index_dir, exist_ok=True)
                self.ix = create_in(self.index_dir, schema)
        else:
            self.ix = create_in(self.index_dir, schema)

    def _tokenize(self, text: str) -> str:
        if not text:
            return ''
        words = jieba.cut(text)
        tokens = []
        for word in words:
            word = word.strip()
            if word and not re.match(r'^[\s\W\d]+$', word):
                tokens.append(word.lower())
        return ' '.join(tokens)

    def add_document(self, doc_id: str, filename: str, chunks: List[Dict],
                     upload_time: Optional[datetime] = None) -> int:
        if upload_time is None:
            upload_time = datetime.now()

        added_count = 0

        writer = self.ix.writer()
        try:
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_{i}"
                content_index = self._tokenize(chunk['text'])
                writer.add_document(
                    doc_id=doc_id,
                    chunk_id=chunk_id,
                    filename=filename,
                    section=chunk.get('section', ''),
                    content=chunk['text'],
                    content_index=content_index,
                    start_pos=chunk.get('start_pos', 0),
                    end_pos=chunk.get('end_pos', 0),
                    chunk_index=i,
                    total_chunks=len(chunks),
                    page=chunk.get('page', 1),
                    upload_time=upload_time
                )
                added_count += 1
            writer.commit()
        except Exception:
            writer.cancel()
            raise

        return added_count

    def delete_document(self, doc_id: str) -> int:
        deleted_count = 0

        writer = self.ix.writer()
        try:
            deleted = writer.delete_by_term('doc_id', doc_id)
            deleted_count = deleted if isinstance(deleted, int) else 0
            writer.commit()
        except Exception:
            writer.cancel()
            raise

        return deleted_count

    def search(self, query_str: str, top_k: int = 3) -> List[Dict]:
        if not query_str or not query_str.strip():
            return []

        query_tokens = self._tokenize_query(query_str)
        if not query_tokens:
            return []

        results_list = []

        with self.ix.searcher(weighting=scoring.BM25F()) as searcher:
            terms = []
            for token in query_tokens:
                if token:
                    terms.append(Term('content_index', token))

            if not terms:
                return []

            query = Or(terms) if len(terms) > 1 else terms[0]
            results = searcher.search(query, limit=top_k)

            for hit in results:
                highlighted = self._highlight_text(hit['content'], query_tokens)

                results_list.append({
                    'doc_id': hit['doc_id'],
                    'chunk_id': hit['chunk_id'],
                    'filename': hit['filename'],
                    'section': hit.get('section', ''),
                    'content': hit['content'],
                    'highlighted': highlighted,
                    'score': float(hit.score),
                    'start_pos': hit['start_pos'],
                    'end_pos': hit['end_pos'],
                    'chunk_index': hit['chunk_index'],
                    'total_chunks': hit['total_chunks'],
                    'page': hit.get('page', 1),
                    'matched_keywords': self._find_matched_keywords(query_tokens, hit['content'])
                })

        return results_list

    def _highlight_text(self, text: str, keywords: List[str]) -> str:
        if not keywords or not text:
            return text

        result = text
        sorted_keywords = sorted(keywords, key=len, reverse=True)

        for keyword in sorted_keywords:
            if not keyword:
                continue
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            result = pattern.sub(f'{{{{HIGHLIGHT}}}}\\g<0>{{{{/HIGHLIGHT}}}}', result)

        result = result.replace('{{HIGHLIGHT}}', '<span class="highlight">')
        result = result.replace('{{/HIGHLIGHT}}', '</span>')

        return result

    def _tokenize_query(self, query_str: str) -> List[str]:
        if not query_str:
            return []

        tokens = []
        words = jieba.cut(query_str.strip())
        seen = set()

        for word in words:
            word = word.strip().lower()
            if word and word not in seen and not re.match(r'^[\s\W\d]+$', word):
                tokens.append(word)
                seen.add(word)

        return tokens

    def _find_matched_keywords(self, query_tokens: List[str], content: str) -> List[str]:
        if not content:
            return []

        content_lower = content.lower()
        matched = []

        for token in query_tokens:
            if token and token.lower() in content_lower:
                matched.append(token)

        return matched

    def get_all_documents(self) -> List[Dict]:
        docs = {}

        with self.ix.searcher() as searcher:
            for docnum in searcher.all_stored_fields():
                doc_id = docnum['doc_id']
                if doc_id not in docs:
                    docs[doc_id] = {
                        'doc_id': doc_id,
                        'filename': docnum['filename'],
                        'upload_time': docnum['upload_time'],
                        'chunk_count': 0
                    }
                docs[doc_id]['chunk_count'] += 1

        return sorted(docs.values(), key=lambda x: x['upload_time'], reverse=True)

    def get_document_count(self) -> int:
        doc_ids = set()

        with self.ix.searcher() as searcher:
            for docnum in searcher.all_stored_fields():
                doc_ids.add(docnum['doc_id'])

        return len(doc_ids)

    def get_chunk_count(self) -> int:
        count = 0
        with self.ix.searcher() as searcher:
            for _ in searcher.all_stored_fields():
                count += 1
        return count

    def get_stats(self) -> Dict:
        return {
            'document_count': self.get_document_count(),
            'chunk_count': self.get_chunk_count()
        }

    def document_exists(self, doc_id: str) -> bool:
        with self.ix.searcher() as searcher:
            for docnum in searcher.all_stored_fields():
                if docnum['doc_id'] == doc_id:
                    return True
        return False
