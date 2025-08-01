# chains/query_interpreter.py

import re
import spacy
from typing import Dict, Optional

class QueryInterpreter:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.common_procedures = [
            "knee surgery", "hip replacement", "cataract surgery",
            "heart bypass", "angioplasty", "appendectomy", "delivery", "fracture"
        ]

    def parse(self, query: str) -> Dict[str, Optional[str]]:
        query = query.lower().strip()
        doc = self.nlp(query)

        parsed = {
            "age": None,
            "gender": None,
            "procedure": None,
            "location": None,
            "policy_duration": None
        }

        # --- AGE ---
        age_match = re.search(r'(\d{1,3})\s*(year[- ]?old|yrs?|y/o)?', query)
        if age_match:
            age = int(age_match.group(1))
            if 0 < age < 120:
                parsed["age"] = str(age)

        # --- GENDER ---
        gender_match = re.search(r'\b(male|female|m|f)\b', query)
        if gender_match:
            g = gender_match.group(1)
            parsed["gender"] = "M" if g.startswith("m") else "F"

        # --- POLICY DURATION ---
        dur_match = re.search(r'(\d{1,2})\s*[- ]?(month|months|year|years)\b', query)
        if dur_match:
            value, unit = dur_match.groups()
            parsed["policy_duration"] = f"{value} {unit}"

        # --- LOCATION ---
        for ent in doc.ents:
            if ent.label_ == "GPE":  # Geo-political entity
                parsed["location"] = ent.text.title()
                break

        # --- PROCEDURE ---
        # Try to detect known medical terms
        for proc in self.common_procedures:
            if proc in query:
                parsed["procedure"] = proc.title()
                break

        # Fallback to longest noun chunk
        if not parsed["procedure"]:
            noun_chunks = [chunk.text.strip() for chunk in doc.noun_chunks if "policy" not in chunk.text.lower()]
            if noun_chunks:
                parsed["procedure"] = max(noun_chunks, key=len).title()

        return parsed
