import os
import re
from typing import List, Dict, Tuple


class DocumentParser:
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.md', '.markdown', '.txt'}

    def __init__(self):
        pass

    def parse(self, file_path: str) -> Dict:
        ext = os.path.splitext(file_path)[1].lower()
        filename = os.path.basename(file_path)

        if ext == '.pdf':
            text, sections = self._parse_pdf(file_path)
        elif ext in ('.docx', '.doc'):
            text, sections = self._parse_docx(file_path)
        elif ext in ('.md', '.markdown'):
            text, sections = self._parse_markdown(file_path)
        elif ext == '.txt':
            text, sections = self._parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        return {
            'filename': filename,
            'full_text': text,
            'sections': sections,
            'file_size': os.path.getsize(file_path),
            'upload_time': os.path.getmtime(file_path)
        }

    def _parse_pdf(self, file_path: str) -> Tuple[str, List[Dict]]:
        from PyPDF2 import PdfReader

        reader = PdfReader(file_path)
        full_text = ""
        sections = []

        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            full_text += page_text + "\n\n"

            lines = page_text.split('\n')
            current_section = None
            section_text = ""

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if self._is_heading(line) and len(line) < 100:
                    if current_section and section_text:
                        sections.append({
                            'title': current_section,
                            'content': section_text.strip(),
                            'page': page_num + 1
                        })
                    current_section = line
                    section_text = ""
                else:
                    section_text += line + "\n"

            if current_section and section_text:
                sections.append({
                    'title': current_section,
                    'content': section_text.strip(),
                    'page': page_num + 1
                })

        if not sections and full_text.strip():
            sections.append({
                'title': os.path.basename(file_path),
                'content': full_text.strip(),
                'page': 1
            })

        return full_text.strip(), sections

    def _parse_docx(self, file_path: str) -> Tuple[str, List[Dict]]:
        from docx import Document

        doc = Document(file_path)
        full_text = ""
        sections = []
        current_section = None
        section_text = ""

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            full_text += text + "\n\n"

            style_name = para.style.name.lower() if para.style else ""
            is_heading = 'heading' in style_name or '标题' in style_name or self._is_heading(text)

            if is_heading and len(text) < 200:
                if current_section and section_text:
                    sections.append({
                        'title': current_section,
                        'content': section_text.strip(),
                        'page': 1
                    })
                current_section = text
                section_text = ""
            else:
                section_text += text + "\n"

        if current_section and section_text:
            sections.append({
                'title': current_section,
                'content': section_text.strip(),
                'page': 1
            })

        if not sections and full_text.strip():
            sections.append({
                'title': os.path.basename(file_path),
                'content': full_text.strip(),
                'page': 1
            })

        return full_text.strip(), sections

    def _parse_markdown(self, file_path: str) -> Tuple[str, List[Dict]]:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        sections = []
        current_section = None
        section_lines = []

        lines = content.split('\n')
        for line in lines:
            if re.match(r'^#{1,6}\s+', line):
                if current_section and section_lines:
                    sections.append({
                        'title': current_section,
                        'content': '\n'.join(section_lines).strip(),
                        'page': 1
                    })
                current_section = re.sub(r'^#{1,6}\s+', '', line).strip()
                section_lines = []
            else:
                section_lines.append(line)

        if current_section and section_lines:
            sections.append({
                'title': current_section,
                'content': '\n'.join(section_lines).strip(),
                'page': 1
            })

        if not sections:
            sections.append({
                'title': os.path.basename(file_path),
                'content': content.strip(),
                'page': 1
            })

        full_text = self._markdown_to_text(content)
        return full_text.strip(), sections

    def _markdown_to_text(self, markdown_content: str) -> str:
        text = markdown_content

        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'`{3}[\s\S]*?`{3}', '', text)
        text = re.sub(r'`(.+?)`', r'\1', text)
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
        text = re.sub(r'^[-*+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text

    def _parse_txt(self, file_path: str) -> Tuple[str, List[Dict]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()

        sections = []
        lines = content.split('\n')
        current_section = None
        section_text = ""

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if section_text:
                    section_text += "\n"
                continue

            if self._is_heading(stripped) and len(stripped) < 100:
                if current_section and section_text:
                    sections.append({
                        'title': current_section,
                        'content': section_text.strip(),
                        'page': 1
                    })
                current_section = stripped
                section_text = ""
            else:
                section_text += stripped + "\n"

        if current_section and section_text:
            sections.append({
                'title': current_section,
                'content': section_text.strip(),
                'page': 1
            })

        if not sections and content.strip():
            sections.append({
                'title': os.path.basename(file_path),
                'content': content.strip(),
                'page': 1
            })

        return content.strip(), sections

    def _is_heading(self, text: str) -> bool:
        if len(text) > 100:
            return False

        if re.match(r'^第[一二三四五六七八九十百千]+[章节篇部分]', text):
            return True

        if re.match(r'^\d+(\.\d+)*\s+', text) and len(text) < 80:
            return True

        if text.endswith('。') or text.endswith('！') or text.endswith('？'):
            return False

        if len(text) < 50 and not any(c in text for c in '，。；：！？,.;:!?'):
            return True

        return False

    @classmethod
    def is_supported(cls, filename: str) -> bool:
        ext = os.path.splitext(filename)[1].lower()
        return ext in cls.SUPPORTED_EXTENSIONS
