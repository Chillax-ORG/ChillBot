import json
import os
import re
from typing import List, Dict

import numpy as np
from sentence_transformers import SentenceTransformer


class FAQManager:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', faq_filename: str = 'faq_entries.json'):
        self.faq_filename = f'storage/{faq_filename}'
        self.model = SentenceTransformer(model_name)
        self.faq_entries: List[Dict[str, str]] = []
        self.faq_embeddings: List[np.ndarray] = []

    def add_entry(self, question: str, answer: str) -> bool:
        for entry in self.faq_entries:
            if entry['question'].lower() == question.lower():
                return False

        self.faq_entries.append({'question': question, 'answer': answer})
        self.faq_embeddings.append(self.model.encode(question, show_progress_bar=False))
        return True

    def update_entry(self, question: str, new_answer: str) -> bool:
        for entry in self.faq_entries:
            if entry['question'].lower() == question.lower():
                entry['answer'] = new_answer
                return True
        return False

    def remove_entry(self, question: str) -> bool:
        for i, entry in enumerate(self.faq_entries):
            if entry['question'].lower() == question.lower():
                del self.faq_entries[i]
                del self.faq_embeddings[i]
                return True
        return False

    def find_most_similar_question(self, user_question: str, threshold: float = 0.75) -> tuple[str | None, float]:
        user_embedding = self.model.encode(user_question, show_progress_bar=False)

        max_similarity = 0
        most_similar_answer = None

        for i, embedding in enumerate(self.faq_embeddings):
            similarity = np.dot(user_embedding, embedding) / (
                np.linalg.norm(user_embedding) * np.linalg.norm(embedding))
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_answer = self.faq_entries[i]['answer']

        return (most_similar_answer, max_similarity) if max_similarity > threshold else (None, 0)

    def split_sentences(self, text):
        text = text.strip()

        # Split on common sentence-ending punctuation followed by a space or newline
        sentences = re.split(r'(?<=[.!?])\s+|\n+|(?<=[.!?])(?=$)', text)

        # Remove empty strings and strip whitespace from each sentence
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def get_answer(self, message: str) -> str | None:
        if len(message) > 1000:
            # Ignore very long messages
            return None
        sentences = self.split_sentences(message)
        answers = []
        for sentence in sentences:
            answers.append(self.find_most_similar_question(sentence))

        if len(answers) == 0:
            return None

        return max(answers, key=lambda x: x[1])[0]

    def save_to_json(self):
        with open(self.faq_filename, 'w') as f:
            json.dump(self.faq_entries, f, indent=2)

    def load_from_json(self):
        # Create file if it doesn't exist
        if not os.path.isfile(self.faq_filename):
            with open(self.faq_filename, 'w') as db:
                db.write(json.dumps({}))

        with open(self.faq_filename, 'r') as f:
            self.faq_entries = json.load(f)
        self.faq_embeddings = [self.model.encode(entry['question'], show_progress_bar=False) for entry in self.faq_entries]
