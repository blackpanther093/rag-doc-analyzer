# chains/decision_chain.py

from query_interpreter import QueryInterpreter
from qa_chain import QAChain  # your existing class
from conv_mem import ConversationMemory
class DecisionChain:
    def __init__(self, config):
        self.memory = ConversationMemory()
        self.interpreter = QueryInterpreter()
        self.qa_chain = QAChain(config)

    def __getattr__(self, name):
        return getattr(self.qachain, name)
    
    def run(self, query: str, retriever, session_id: str):
        structured_query = self.interpreter.parse(query)

        # Optionally, inject structured_query into logs or context
        print(f"🔍 Parsed Query: {structured_query}")

        # You could even enrich the query before passing to QAChain
        enriched_query = self._enrich_query(query, structured_query)

        return self.qa_chain.run(enriched_query, retriever, session_id)

    def _enrich_query(self, original: str, parsed: dict) -> str:
        # Optionally embed structured data into question for LLM context
        additions = []
        for k, v in parsed.items():
            if v:
                additions.append(f"{k.replace('_', ' ').title()}: {v}")
        metadata_str = "\n".join(additions)
        return f"{original}\n\n[Metadata]\n{metadata_str}"
