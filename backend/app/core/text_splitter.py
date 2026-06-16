import re
from typing import List, Dict


class TextSplitter:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        if not text or not text.strip():
            return []

        metadata = metadata or {}
        chunks = []

        paragraphs = self._split_paragraphs(text)

        current_chunk = ""
        current_start = 0

        for para in paragraphs:
            if not para.strip():
                continue

            if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                if current_chunk:
                    current_chunk += "\n\n"
                current_chunk += para
            else:
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'start_pos': current_start,
                        'end_pos': current_start + len(current_chunk),
                        'section': metadata.get('section', '')
                    })

                    overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                    current_chunk = current_chunk[overlap_start:] + "\n\n" + para
                    current_start = current_start + overlap_start
                else:
                    sub_chunks = self._split_long_paragraph(para, current_start)
                    chunks.extend(sub_chunks)
                    if sub_chunks:
                        last_chunk = sub_chunks[-1]
                        overlap_start = max(0, len(last_chunk['text']) - self.chunk_overlap)
                        current_chunk = last_chunk['text'][overlap_start:]
                        current_start = last_chunk['start_pos'] + overlap_start
                    else:
                        current_chunk = ""
                        current_start = 0

        if current_chunk and current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'start_pos': current_start,
                'end_pos': current_start + len(current_chunk),
                'section': metadata.get('section', '')
            })

        for i, chunk in enumerate(chunks):
            chunk['chunk_index'] = i
            chunk['total_chunks'] = len(chunks)

        return chunks

    def split_sections(self, sections: List[Dict]) -> List[Dict]:
        all_chunks = []

        for section in sections:
            section_text = section.get('content', '')
            section_title = section.get('title', '')

            if not section_text or not section_text.strip():
                continue

            chunks = self.split_text(
                section_text,
                metadata={'section': section_title}
            )

            for chunk in chunks:
                chunk['page'] = section.get('page', 1)
                all_chunks.append(chunk)

        return all_chunks

    def _split_paragraphs(self, text: str) -> List[str]:
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_long_paragraph(self, para: str, start_offset: int = 0) -> List[Dict]:
        chunks = []
        current_pos = 0
        para_len = len(para)

        while current_pos < para_len:
            end_pos = min(current_pos + self.chunk_size, para_len)

            if end_pos < para_len:
                break_points = [
                    para.rfind('。', current_pos, end_pos),
                    para.rfind('！', current_pos, end_pos),
                    para.rfind('？', current_pos, end_pos),
                    para.rfind('. ', current_pos, end_pos),
                    para.rfind('! ', current_pos, end_pos),
                    para.rfind('? ', current_pos, end_pos),
                    para.rfind('\n', current_pos, end_pos),
                ]

                valid_breaks = [b for b in break_points if b > current_pos + self.chunk_size // 2]
                if valid_breaks:
                    end_pos = max(valid_breaks) + 1

            chunk_text = para[current_pos:end_pos].strip()
            if chunk_text:
                chunks.append({
                    'text': chunk_text,
                    'start_pos': start_offset + current_pos,
                    'end_pos': start_offset + end_pos,
                    'section': ''
                })

            if end_pos >= para_len:
                break

            current_pos = end_pos - self.chunk_overlap
            if current_pos < 0:
                current_pos = 0
            if current_pos == end_pos - self.chunk_overlap and end_pos == para_len:
                break

        return chunks
