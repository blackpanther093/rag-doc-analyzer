import os, re
import logging
import traceback
from typing import Dict, Any
from conv_mem import ConversationMemory
from setup_api import logger
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

# -----------------------------
# QA Chain
# -----------------------------
class QAChain:
    """Handles question answering with retrieval and memory"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.memory = ConversationMemory()
        self.llm = ChatGroq(
            api_key=config['GROQ_API_KEY'],
            model_name=config['LLM_MODEL'],
            max_tokens=4000,
            temperature=0.1
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are a helpful assistant that answers questions based on the provided context. "
                "Use only the information from the context to answer questions. "
                "If you cannot find the answer in the context, reply with 'I don't know based on the provided documents.' "
                "Be concise but comprehensive in your answers.\n\n"
                "Context: {context}"
            )),
            ("human", "{question}")
        ])
        
        logger.info("QA Chain initialized")
    
    def _extract_decision(self, answer: str) -> str:
                    ans = answer.lower()
                    if "not covered" in ans or "not eligible" in ans or "rejected" in ans:
                        return "Rejected"
                    elif "covered" in ans or "eligible" in ans or "approved" in ans:
                        return "Approved"
                    elif "depends" in ans or "cannot determine" in ans:
                        return "Unclear"
                    else:
                        return "Unknown"

    def _extract_amount(self, answer: str) -> str:
        match = re.search(r'(₹|\$|Rs\.?)\s?\d{1,3}(,\d{3})*', answer)
        return match.group(0) if match else "N/A"
    
    def run(self, question: str, retriever, session_id: str) -> Dict[str, Any]:
        """Process question and return answer with history"""
        if not question or not question.strip():
            return {
                'answer': "Please enter a valid question.",
                'history': self.memory.get_history(session_id)
            }
        
        try:
            # Add human message to memory
            self.memory.add_message(session_id, 'human', question)
            
            # Retrieve relevant documents
            docs = []
            try:
                docs = retriever.get_relevant_documents(question)
                logger.info(f"Retrieved {len(docs)} documents for question")
            except Exception as e:
                logger.error(f"Document retrieval failed: {e}")
            
            # Prepare context
            context = "\n---\n".join([doc.page_content for doc in docs])
            
            # Generate answer
            try:
                formatted_prompt = self.prompt.format_prompt(
                    context=context, 
                    question=question
                )
                
                response = self.llm.invoke(formatted_prompt.to_messages())
                answer = response.content

            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                answer = "I apologize, but I encountered an error while generating the answer. Please try again."
            
            # Add AI response to memory
            self.memory.add_message(session_id, 'assistant', answer)
            
            return {
                "decision": self._extract_decision(answer),
                "amount": self._extract_amount(answer),
                "justification": answer.strip(),

                "evidence_clauses": [
                    {
                        "text": doc.page_content,
                        "metadata": doc.metadata
                    } for doc in docs
                ],

                "query_details": {
                    "interpreted_from": question
                    # You can replace this with structured fields from QueryInterpreter later
                },

                "answer": answer,
                "history": self.memory.get_history(session_id)
            }

            
        except Exception as e:
            logger.error(f"QA chain execution failed: {e}")
            return {
                'answer': "An error occurred while processing your question. Please try again.",
                'history': self.memory.get_history(session_id)
            }

