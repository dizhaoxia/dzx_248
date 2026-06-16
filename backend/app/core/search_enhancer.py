import os
import json
import re
import jieba
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import Counter


class SearchEnhancer:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.synonyms_path = os.path.join(self.data_dir, 'synonyms.json')
        self.word_freq_path = os.path.join(self.data_dir, 'word_frequency.json')
        self.query_history_path = os.path.join(self.data_dir, 'query_history.json')
        
        self.synonyms = self._load_json(self.synonyms_path, {})
        self.word_freq = self._load_json(self.word_freq_path, {})
        self.query_history = self._load_json(self.query_history_path, [])

    def _load_json(self, path: str, default):
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return default
        return default

    def _save_json(self, path: str, data):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def expand_query_with_synonyms(self, query_str: str) -> Tuple[str, List[str]]:
        tokens = list(jieba.cut(query_str.strip()))
        expanded_tokens = []
        all_keywords = []
        
        for token in tokens:
            token = token.strip()
            if not token:
                continue
            
            expanded_tokens.append(token)
            all_keywords.append(token)
            
            if token in self.synonyms:
                for syn in self.synonyms[token]:
                    if syn not in expanded_tokens:
                        expanded_tokens.append(syn)
                        all_keywords.append(syn)
        
        expanded_query = ' '.join(expanded_tokens)
        return expanded_query, list(set(all_keywords))

    def get_synonyms(self, word: str) -> List[str]:
        return self.synonyms.get(word, [])

    def add_synonym(self, word: str, synonym: str):
        if word not in self.synonyms:
            self.synonyms[word] = []
        if synonym not in self.synonyms[word]:
            self.synonyms[word].append(synonym)
        self._save_json(self.synonyms_path, self.synonyms)

    def remove_synonym(self, word: str, synonym: str):
        if word in self.synonyms and synonym in self.synonyms[word]:
            self.synonyms[word].remove(synonym)
            self._save_json(self.synonyms_path, self.synonyms)

    def get_all_synonyms(self) -> Dict[str, List[str]]:
        return self.synonyms

    def update_synonyms_dict(self, synonyms_dict: Dict[str, List[str]]):
        self.synonyms = synonyms_dict
        self._save_json(self.synonyms_path, self.synonyms)

    def extract_phrases(self, query_str: str) -> List[str]:
        tokens = list(jieba.cut(query_str.strip()))
        tokens = [t.strip() for t in tokens if t.strip() and not re.match(r'^[\s\W\d]+$', t)]
        
        phrases = []
        for i in range(len(tokens) - 1):
            phrase = tokens[i] + tokens[i + 1]
            phrases.append(phrase)
        
        for i in range(len(tokens) - 2):
            phrase = tokens[i] + tokens[i + 1] + tokens[i + 2]
            phrases.append(phrase)
        
        return phrases

    def calculate_phrase_boost(self, content: str, phrases: List[str]) -> float:
        if not phrases:
            return 1.0
        
        content_lower = content.lower()
        boost = 1.0
        hit_count = 0
        
        for phrase in phrases:
            if phrase.lower() in content_lower:
                hit_count += 1
        
        if hit_count > 0:
            boost = 1.0 + (hit_count * 0.3)
        
        return boost

    def extract_focus_sentences(self, content: str, keywords: List[str], 
                                max_sentences: int = 2) -> Tuple[str, List[str]]:
        if not content or not keywords:
            return content, []
        
        sentences = self._split_sentences(content)
        if not sentences:
            return content, []
        
        keyword_lower = [k.lower() for k in keywords if k.strip()]
        
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()
            score = 0
            matched = []
            
            for kw in keyword_lower:
                if kw in sentence_lower:
                    count = sentence_lower.count(kw)
                    score += count * len(kw)
                    matched.append(kw)
            
            if score > 0:
                score += (1.0 / (i + 1))
                scored_sentences.append((score, i, sentence, matched))
        
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        
        if not scored_sentences:
            return sentences[0] if sentences else content, []
        
        top_indices = sorted([s[1] for s in scored_sentences[:max_sentences]])
        
        result_sentences = []
        all_matched = set()
        
        for idx in top_indices:
            result_sentences.append(sentences[idx])
            
        for s in scored_sentences[:max_sentences]:
            all_matched.update(s[3])
        
        focus_text = ''.join(result_sentences).strip()
        
        if len(focus_text) < 50 and len(sentences) > top_indices[-1] + 1:
            next_idx = top_indices[-1] + 1
            if next_idx < len(sentences):
                focus_text += sentences[next_idx]
        
        return focus_text, list(all_matched)

    def _split_sentences(self, text: str) -> List[str]:
        if not text:
            return []
        
        pattern = r'([。！？!?\n]+)'
        parts = re.split(pattern, text)
        
        sentences = []
        for i in range(0, len(parts) - 1, 2):
            if parts[i].strip():
                sentence = parts[i].strip() + parts[i + 1]
                sentences.append(sentence)
        
        if len(parts) % 2 == 1 and parts[-1].strip():
            sentences.append(parts[-1].strip())
        
        if not sentences:
            sentences = [text.strip()]
        
        return sentences

    def levenshtein_distance(self, s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]

    def correct_spelling(self, query_str: str) -> Tuple[Optional[str], List[Dict]]:
        query_str = query_str.strip()
        if not query_str:
            return None, []
        
        tokens = list(jieba.cut(query_str))
        tokens = [t.strip() for t in tokens if t.strip()]
        
        if not tokens:
            return None, []
        
        corrections = []
        all_correct = True
        corrected_parts = []
        
        for token in tokens:
            if len(token) < 2:
                corrected_parts.append(token)
                continue
            
            if token in self.word_freq:
                corrected_parts.append(token)
                continue
            
            all_correct = False
            candidates = []
            
            for word, freq in self.word_freq.items():
                if abs(len(word) - len(token)) > 1:
                    continue
                
                dist = self.levenshtein_distance(token, word)
                if dist == 1:
                    score = (1.0 / (dist + 1)) * (freq / 1000.0)
                    candidates.append({
                        'word': word,
                        'distance': dist,
                        'frequency': freq,
                        'score': score
                    })
            
            candidates.sort(key=lambda x: x['score'], reverse=True)
            
            if candidates and candidates[0]['score'] > 0.1:
                corr_item = {
                    'original': token,
                    'suggestions': candidates[:3]
                }
                corrections.append(corr_item)
                corrected_parts.append(candidates[0]['word'])
            else:
                corrected_parts.append(token)
        
        if all_correct:
            return None, []
        
        corrected_query = ''.join(corrected_parts)
        
        if corrected_query == query_str:
            return None, []
        
        return corrected_query, corrections

    def find_similar_queries(self, query_str: str, top_k: int = 5) -> List[Dict]:
        if not query_str or not self.query_history:
            return []
        
        query_tokens = set()
        for word in jieba.cut(query_str.strip()):
            word = word.strip().lower()
            if word and not re.match(r'^[\s\W\d]+$', word):
                query_tokens.add(word)
        
        if not query_tokens:
            return []
        
        scored_queries = []
        
        for item in self.query_history:
            history_query = item.get('query', '')
            if not history_query or history_query == query_str:
                continue
            
            history_tokens = set()
            for word in jieba.cut(history_query):
                word = word.strip().lower()
                if word and not re.match(r'^[\s\W\d]+$', word):
                    history_tokens.add(word)
            
            if not history_tokens:
                continue
            
            intersection = query_tokens & history_tokens
            union = query_tokens | history_tokens
            
            if len(union) == 0:
                continue
            
            jaccard = len(intersection) / len(union)
            
            overlap_count = len(intersection)
            count_boost = item.get('count', 1) * 0.01
            
            final_score = jaccard + (overlap_count * 0.1) + count_boost
            
            if final_score > 0.1:
                scored_queries.append({
                    'query': history_query,
                    'score': round(final_score, 4),
                    'overlap_count': overlap_count,
                    'overlap_words': list(intersection),
                    'count': item.get('count', 1)
                })
        
        scored_queries.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_queries[:top_k]

    def record_query(self, query_str: str):
        if not query_str or not query_str.strip():
            return
        
        query_str = query_str.strip()
        
        found = False
        for item in self.query_history:
            if item.get('query') == query_str:
                item['count'] = item.get('count', 0) + 1
                item['last_time'] = datetime.now().isoformat()
                found = True
                break
        
        if not found:
            self.query_history.append({
                'query': query_str,
                'count': 1,
                'last_time': datetime.now().isoformat()
            })
        
        self._save_json(self.query_history_path, self.query_history)

    def get_query_history(self, limit: int = 50) -> List[Dict]:
        sorted_history = sorted(
            self.query_history, 
            key=lambda x: x.get('count', 0), 
            reverse=True
        )
        return sorted_history[:limit]

    def clear_query_history(self):
        self.query_history = []
        self._save_json(self.query_history_path, self.query_history)
