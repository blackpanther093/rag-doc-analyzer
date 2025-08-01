import os
from datetime import datetime
from typing import List, Any, Dict, Union, Optional
import logging
import traceback
from PyPDF2 import PdfReader
import fitz  # PyMuPDF

from setup_api import logger

# -----------------------------
# File Processing
# -----------------------------
class FileProcessor:
    """Handles file upload and text extraction"""
    
    @staticmethod
    def extract_text(files: List[Any], use_ocr: bool = False) -> str:
        """Extract text from uploaded files"""
        if not files:
            return ""
        
        combined_texts = []
        processed_count = 0
        
        for file_obj in files:
            try:
                filename = getattr(file_obj, 'name', 'unknown')
                logger.info(f"Processing file: {filename}")
                
                # Determine file type
                file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
                
                content = ""
                
                # Process based on file type
                if file_extension == 'pdf':
                    content = FileProcessor._extract_pdf(file_obj)
                elif file_extension == 'txt':
                    content = FileProcessor._extract_text_file(file_obj)
                elif file_extension in ['png', 'jpg', 'jpeg'] and use_ocr:
                    content = FileProcessor._extract_image_ocr(file_obj)
                elif file_extension in ['png', 'jpg', 'jpeg'] and not use_ocr:
                    logger.info(f"Skipping image {filename} - OCR not enabled")
                    continue
                else:
                    logger.warning(f"Unsupported file type: {file_extension} for {filename}")
                    continue
                
                if content and content.strip():
                    combined_texts.append(f"=== Content from {filename} ===\n{content}")
                    processed_count += 1
                    logger.info(f"Successfully extracted text from {filename} ({len(content)} characters)")
                else:
                    logger.warning(f"No text extracted from {filename}")
                    
            except Exception as e:
                logger.error(f"Error processing file {getattr(file_obj, 'name', 'unknown')}: {str(e)}")
                logger.error(traceback.format_exc())
        
        result = "\n\n".join(combined_texts)
        logger.info(f"Processed {processed_count} files, total text length: {len(result)}")
        return result

    @staticmethod
    def _extract_pdf(file_obj: Any) -> str:
        """Extract text from PDF file"""
        try:
            # First try PyPDF2
            if hasattr(file_obj, 'read'):
                file_obj.seek(0)
            
            reader = PdfReader(file_obj)
            texts = []
            
            for page_num, page in enumerate(reader.pages):
                try:
                    text = page.extract_text()
                    if text:
                        texts.append(text)
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num}: {e}")
            
            text = "\n".join(texts)
            
            # If PyPDF2 didn't work well, try PyMuPDF
            if not text.strip():
                logger.info("PyPDF2 extraction resulted in empty text, trying PyMuPDF")
                if hasattr(file_obj, 'read'):
                    file_obj.seek(0)
                    pdf_bytes = file_obj.read()
                else:
                    with open(file_obj, 'rb') as f:
                        pdf_bytes = f.read()
                
                doc = fitz.open(stream=pdf_bytes, filetype='pdf')
                texts = []
                for page in doc:
                    texts.append(page.get_text())
                doc.close()
                text = "\n".join(texts)
            
            return text
            
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return ""

    @staticmethod
    def _extract_text_file(file_obj: Any) -> str:
        """Extract text from plain text file"""
        try:
            if hasattr(file_obj, 'read'):
                content = file_obj.read()
            else:
                with open(file_obj, 'rb') as f:
                    content = f.read()
            
            # Try to decode as UTF-8, fallback to other encodings
            if isinstance(content, bytes):
                try:
                    return content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        return content.decode('latin-1')
                    except UnicodeDecodeError:
                        return content.decode('utf-8', errors='ignore')
            
            return str(content)
            
        except Exception as e:
            logger.error(f"Text file extraction failed: {e}")
            return ""

    @staticmethod
    def _extract_image_ocr(file_obj: Any) -> str:
        """Extract text from image using OCR"""
        try:
            from PIL import Image
            import pytesseract
            
            if hasattr(file_obj, 'read'):
                file_obj.seek(0)
                img = Image.open(file_obj)
            else:
                img = Image.open(file_obj)
            
            text = pytesseract.image_to_string(img)
            return text
            
        except ImportError:
            logger.error("pytesseract not installed. Please install it for OCR support: pip install pytesseract")
            return ""
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""
