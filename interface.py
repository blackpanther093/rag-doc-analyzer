import traceback
import uuid
from setup_api import APIKeyManager, logger
from file_processing import FileProcessor
from text_processing import TextProcessor
from app_state import app_state
import gradio as gr


# -----------------------------
# Gradio Interface Functions
# -----------------------------

def upload_and_index(files, use_ocr, progress=gr.Progress()):
    """Handle file upload and indexing"""
    try:
        if not files or len(files) == 0:
            return "❌ No files uploaded.", gr.update(interactive=False)
        
        progress(0.1, desc="Extracting text from files...")
        
        # Extract text from files
        raw_text = FileProcessor.extract_text(files, use_ocr)
        
        if not raw_text.strip():
            return "❌ Failed to extract any text from uploaded files.", gr.update(interactive=False)
        
        progress(0.4, desc="Cleaning and processing text...")
        
        # Clean and chunk text
        clean_text = TextProcessor.clean(raw_text)
        chunks = TextProcessor.chunk(clean_text)
        
        if not chunks:
            return "❌ No text chunks generated.", gr.update(interactive=False)
        
        progress(0.7, desc="Creating embeddings and indexing...")
        
        # Add to vector store
        indexed_count = app_state.vector_store.add_documents(chunks, app_state.session_id)
        
        progress(1.0, desc="Indexing complete!")
        
        # Update application state
        app_state.documents_indexed = True
        
        return (
            f"✅ Successfully indexed {indexed_count} chunks from {len(files)} file(s).",
            gr.update(interactive=True)
        )
        
    except Exception as e:
        logger.error(f"Upload and indexing failed: {e}")
        logger.error(traceback.format_exc())
        return f"❌ Error during indexing: {str(e)}", gr.update(interactive=False)

def ask_question(question, chat_history):
    """Handle question asking and return updated chat"""
    try:
        if not app_state.documents_indexed:
            return chat_history, "Please upload and index documents first.", ""
        
        if not question or not question.strip():
            return chat_history, "Please enter a valid question.", ""
        
        # Get retriever
        retriever = app_state.vector_store.get_retriever(app_state.session_id)
        
        # Run QA chain
        result = app_state.qa_chain.run(question, retriever, app_state.session_id)
        
        # Update chat history
        updated_history = []
        for msg in result['history']:
            role = "You" if msg['role'] == 'human' else "Assistant"
            updated_history.append([msg['content'], None] if msg['role'] == 'human' else [None, msg['content']])
        
        return updated_history, result['answer'], ""
        
    except Exception as e:
        logger.error(f"Question processing failed: {e}")
        logger.error(traceback.format_exc())
        error_msg = f"Error processing question: {str(e)}"
        return chat_history, error_msg, ""

def reset_session():
    """Reset the current session"""
    global app_state
    old_session = app_state.session_id
    app_state.session_id = str(uuid.uuid4())
    app_state.documents_indexed = False
    
    if app_state.qa_chain:
        app_state.qa_chain.memory.clear_session(old_session)
    
    logger.info(f"Session reset: {old_session} -> {app_state.session_id}")
    
    return (
        "✅ Session reset successfully. Please upload new documents.",
        gr.update(interactive=False),
        [],
        "",
        ""
    )

# -----------------------------
# Build Gradio Interface
# -----------------------------

def build_interface():
    """Build and return Gradio interface"""
    
    # Custom CSS for better styling
    css = """
    .gradio-container {
        max-width: 1200px !important;
    }
    
    .chat-message {
        padding: 10px;
        margin: 5px 0;
        border-radius: 10px;
        max-width: 80%;
    }
    
    .user-message {
        background-color: #007bff;
        color: white;
        margin-left: auto;
        text-align: right;
    }
    
    .bot-message {
        background-color: #f8f9fa;
        color: #333;
        margin-right: auto;
        border: 1px solid #dee2e6;
    }
    
    .upload-area {
        border: 2px dashed #007bff;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        background-color: #f8f9fa;
    }
    
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    
    .header-title {
        background: linear-gradient(45deg, #007bff, #0056b3);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    """
    
    with gr.Blocks(css=css, title="Document Q&A Assistant") as interface:
        
        # Header
        gr.HTML("""
        <div class="header-title">
            <h1>📚 Robust Document Q&A Assistant</h1>
            <p>Upload documents (PDF, TXT, Images) and ask questions about their content</p>
        </div>
        """)
        
        with gr.Row():
            # Left Column - Upload and Index
            with gr.Column(scale=1):
                gr.Markdown("### 📁 Document Upload & Processing")
                
                with gr.Group():
                    file_input = gr.File(
                        file_count="multiple",
                        file_types=[".pdf", ".txt", ".png", ".jpg", ".jpeg"],
                        label="Upload Documents",
                        elem_classes=["upload-area"]
                    )
                    
                    ocr_toggle = gr.Checkbox(
                        label="Enable OCR for Images",
                        value=False,
                        info="Extract text from image files using OCR"
                    )
                    
                    with gr.Row():
                        index_btn = gr.Button(
                            "🔄 Process & Index Documents",
                            variant="primary",
                            size="lg"
                        )
                        reset_btn = gr.Button(
                            "🔄 Reset Session",
                            variant="secondary"
                        )
                    
                    status_output = gr.Textbox(
                        label="Status",
                        interactive=False,
                        show_label=True,
                        lines=3
                    )
            
            # Right Column - Chat Interface
            with gr.Column(scale=2):
                gr.Markdown("### 💬 Ask Questions")
                
                chatbot = gr.Chatbot(
                    height=400,
                    label="Conversation",
                    show_label=True,
                    bubble_full_width=False
                )
                
                with gr.Row():
                    question_input = gr.Textbox(
                        label="Your Question",
                        placeholder="Ask a question about your documents...",
                        interactive=False,
                        scale=4
                    )
                    send_btn = gr.Button(
                        "📤 Send",
                        variant="primary",
                        interactive=False,
                        scale=1
                    )
                
                answer_output = gr.Textbox(
                    label="Latest Answer",
                    interactive=False,
                    lines=4,
                    show_label=True
                )
        
        # Event handlers
        index_btn.click(
            fn=upload_and_index,
            inputs=[file_input, ocr_toggle],
            outputs=[status_output, send_btn]
        ).then(
            fn=lambda: gr.update(interactive=True),
            outputs=[question_input]
        )
        
        send_btn.click(
            fn=ask_question,
            inputs=[question_input, chatbot],
            outputs=[chatbot, answer_output, question_input]
        )
        
        question_input.submit(
            fn=ask_question,
            inputs=[question_input, chatbot],
            outputs=[chatbot, answer_output, question_input]
        )
        
        reset_btn.click(
            fn=reset_session,
            outputs=[status_output, send_btn, chatbot, answer_output, question_input]
        )
        
        # Add information footer
        gr.Markdown("""
        ---
        ### 📋 Instructions:
        1. **Upload Documents**: Select PDF, TXT, or image files
        2. **Enable OCR**: Check this option to extract text from images
        3. **Process & Index**: Click to process and index your documents
        4. **Ask Questions**: Once indexed, ask questions about your documents
        5. **Reset Session**: Start over with new documents
        
        ### 🔧 Supported File Types:
        - **PDF**: Documents and papers
        - **TXT**: Plain text files
        - **Images**: PNG, JPG, JPEG (with OCR enabled)
        """)
    
    return interface
