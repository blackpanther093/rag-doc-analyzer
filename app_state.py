import uuid
import os
from setup_api import APIKeyManager, logger
from vectorstore import VectorStore
# from qa_chain import QAChain
from decision_chain import DecisionChain
# -----------------------------
# Application State
# -----------------------------
class AppState:
    """Global application state"""
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.documents_indexed = False
        self.config = None
        self.vector_store = None
        self.qa_chain = None
    
    def initialize(self):
        """Initialize application components"""
        try:
            self.config = APIKeyManager.load_and_validate()
            self.vector_store = VectorStore(self.config)
            self.qa_chain = DecisionChain(self.config)
            logger.info(f"Application initialized with session ID: {self.session_id}")
            return True
        except Exception as e:
            logger.error(f"Application initialization failed: {e}")
            return False

# Global application state
app_state = AppState()
