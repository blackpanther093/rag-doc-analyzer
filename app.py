import traceback
from setup_api import logger
from app_state import app_state
from interface import build_interface
# -----------------------------
# Main Application
# -----------------------------

def main():
    """Main application entry point"""
    try:
        logger.info("Starting Document Q&A Assistant")
        
        # Initialize application
        if not app_state.initialize():
            logger.error("Failed to initialize application")
            return
        
        # Build and launch interface
        interface = build_interface()
        
        logger.info("Launching Gradio interface...")
        interface.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            debug=False,
            show_error=True
        )
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    main()