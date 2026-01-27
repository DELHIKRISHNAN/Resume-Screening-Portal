"""
Utility functions for text extraction and file processing
"""

import os
import re
import logging
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
from docx import Document

logger = logging.getLogger(__name__)


def extract_text_from_file(file_path):
    """
    Extract text from PDF, DOCX, image, or TXT files
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: Extracted text content
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == ".pdf":
            return extract_text_from_pdf(file_path)
        elif ext == ".docx":
            return extract_text_from_docx(file_path)
        elif ext in [".jpg", ".png", ".jpeg"]:
            return extract_text_from_image(file_path)
        elif ext == ".txt":
            return extract_text_from_txt(file_path)
        else:
            logger.warning(f"Unsupported file type: {ext}")
            return ""
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}")
        return ""


def extract_text_from_pdf(file_path):
    """Extract text from PDF file using PyMuPDF"""
    doc = fitz.open(file_path)
    return " ".join(page.get_text() for page in doc)


def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    doc = Document(file_path)
    return " ".join([paragraph.text for paragraph in doc.paragraphs])


def extract_text_from_image(file_path):
    """Extract text from image using OCR (pytesseract)"""
    return pytesseract.image_to_string(Image.open(file_path))


def extract_text_from_txt(file_path):
    """Extract text from TXT file"""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def clean_text(text):
    """
    Basic text cleanup - remove excessive whitespace
    
    Args:
        text (str): Raw text
        
    Returns:
        str: Cleaned text
    """
    return text.replace('\n', ' ').strip()


def clean_sentence(sentence):
    """
    Clean individual sentence for embedding
    
    Args:
        sentence (str): Raw sentence
        
    Returns:
        str: Cleaned sentence
    """
    sentence = sentence.replace('\n', ' ').strip()
    sentence = re.sub(r'\s+', ' ', sentence)
    sentence = re.sub(r'[^\w\s.,;!?/-]', '', sentence)
    return sentence


def extract_relevant_text(text):
    """
    Extract only job-relevant lines (skills, projects, experience, etc.)
    
    Args:
        text (str): Full document text
        
    Returns:
        str: Filtered relevant text
    """
    keywords = ['skills', 'projects', 'experience', 'responsibilities', 'requirements']
    lines = text.splitlines()
    relevant = [line for line in lines if any(k in line.lower() for k in keywords) or len(line.split()) > 5]
    filtered = " ".join(relevant)
    return filtered if len(filtered.split()) >= 50 else text


def sanitize_filename(filename):
    """
    Sanitize uploaded filename to prevent path traversal attacks
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Safe filename
    """
    # Remove any directory path components
    filename = os.path.basename(filename)
    
    # Remove any non-alphanumeric characters except dots, dashes, and underscores
    filename = re.sub(r'[^\w\s.-]', '', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Limit length
    name, ext = os.path.splitext(filename)
    if len(name) > 200:
        name = name[:200]
    
    return name + ext


def validate_file(file, max_size=10*1024*1024, allowed_extensions=None):
    """
    Validate uploaded file size and type
    
    Args:
        file: Django UploadedFile object
        max_size (int): Maximum file size in bytes (default 10MB)
        allowed_extensions (list): List of allowed extensions (default: PDF, DOCX, TXT, images)
        
    Returns:
        tuple: (is_valid: bool, message: str)
    """
    if allowed_extensions is None:
        allowed_extensions = ['.pdf', '.docx', '.txt', '.png', '.jpg', '.jpeg']
    
    if file.size > max_size:
        return False, f"File size exceeds {max_size // (1024*1024)}MB limit"
    
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        return False, f"File type {ext} not supported. Allowed: {', '.join(allowed_extensions)}"
    
    return True, "Valid"


def are_texts_identical(text1, text2, threshold=0.95):
    """
    Check if two texts are identical or nearly identical
    
    Args:
        text1 (str): First text
        text2 (str): Second text
        threshold (float): Similarity threshold (0-1)
        
    Returns:
        bool: True if texts are nearly identical
    """
    # Normalize texts
    clean1 = re.sub(r'\s+', ' ', text1.lower().strip())
    clean2 = re.sub(r'\s+', ' ', text2.lower().strip())
    
    # Check exact match
    if clean1 == clean2:
        return True
    
    # Check character-level similarity
    from difflib import SequenceMatcher
    similarity = SequenceMatcher(None, clean1, clean2).ratio()
    
    return similarity >= threshold
