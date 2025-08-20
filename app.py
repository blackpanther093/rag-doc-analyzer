import traceback
import threading
from src.api.setup_api import logger
from src.utils.app_state import app_state
from src.interfaces.interface import build_interface
from src.api.endpoints import APIEndpoints

# -----------------------------
# Main Application
# -----------------------------

def start_api_server():
    """Start the API server in a separate thread"""
    try:
        # Create API endpoints
        api_endpoints = APIEndpoints(
            qa_chain=app_state.qa_chain,
            cache_manager=app_state.cache_manager,
            security_manager=app_state.security_manager
        )
        
        logger.info("API server starting on port 5000 (background)")
        # Run API server silently without showing Flask messages
        api_endpoints.run(host="127.0.0.1", port=5000, debug=False)
    except Exception as e:
        logger.error(f"API server failed to start: {e}")

def main():
    """Main application entry point"""
    try:
        logger.info("Starting Document Q&A Assistant")
        
        # Initialize application
        if not app_state.initialize():
            logger.error("Failed to initialize application")
            return
        
        # Start API server in a separate thread (silently)
        api_thread = threading.Thread(target=start_api_server, daemon=True)
        api_thread.start()
        
        # Wait a moment for API server to start
        import time
        time.sleep(2)
        
        # Build and launch interface
        interface = build_interface()
        
        logger.info("Launching Gradio interface...")
        print("\n" + "="*60)
        print("🚀 Document Q&A Assistant")
        print("="*60)
        print("📱 Gradio Interface: http://localhost:7860")
        print("🔗 API Server: http://localhost:5000 (background)")
        print("="*60)
        print("💡 Webhook testing: Configure webhook in Gradio interface")
        print("📋 Then ask questions to trigger webhooks!")
        print("="*60 + "\n")
        
        interface.launch(
            server_name="127.0.0.1",
            server_port=7860,
            share=False,
            debug=False,
            show_error=True,
            quiet=True  # Reduce Gradio output
        )
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    main()