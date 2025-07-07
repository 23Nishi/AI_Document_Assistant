import os
import state
import hashlib
import time
import logging
from pdfminer.high_level import extract_text
from transformers import pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load model once at module level
try:
    logger.info("Loading summarization model...")
    summarizer = pipeline("summarization", model="t5-small")
    logger.info("Summarization model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load summarization model: {e}")
    summarizer = None

# Cache for extracted text
text_cache = {}
MAX_CACHE_SIZE = 50

def get_file_stats_key(file_path):
    """Generate a cache key based on file path and modification time"""
    try:
        stat = os.stat(file_path)
        return f"{file_path}_{stat.st_mtime}_{stat.st_size}"
    except Exception as e:
        logger.error(f"Error getting file stats: {e}")
        return None

def cleanup_text_cache():
    """Clean up old cache entries"""
    if len(text_cache) > MAX_CACHE_SIZE:
        
        items = list(text_cache.items())
        text_cache.clear()
        text_cache.update(items[-MAX_CACHE_SIZE:])

# Extract text from the uploaded file
def get_extracted_text():
    file_path = state.uploaded_file_path
    if not file_path:
        return "No file uploaded yet."
    
    if not os.path.exists(file_path):
        return "File not found."
    
    # Generate cache key based on file stats
    cache_key = get_file_stats_key(file_path)
    if not cache_key:
        return "Error processing file."
    
    # Check cache first
    if cache_key in text_cache:
        logger.info(f"Text extraction cache hit for {os.path.basename(file_path)}")
        return text_cache[cache_key]
    
    # Extract text
    start_time = time.time()
    try:
        ext = os.path.splitext(file_path)[-1].lower()

        if ext == ".pdf":
            text = extract_text(file_path)
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            return "Unsupported file format."
        
        # Cache the extracted text
        text_cache[cache_key] = text
        cleanup_text_cache()
        
        end_time = time.time()
        logger.info(f"Text extracted and cached in {end_time - start_time:.2f} seconds")
        
        return text
        
    except Exception as e:
        logger.error(f"Error extracting text: {e}")
        return f"Error extracting text: {str(e)}"


# Generate a summary (max 150 words)
def generate_summary():
    if not summarizer:
        return "Summarization model not available."
    
    text = get_extracted_text()
    
    if text == "No file uploaded yet.":
        return "Please upload a document first."
    
    if text.startswith("Error"):
        return text
    
    # Handle empty or very short text
    if len(text.strip()) < 50:
        return "Document is too short to generate a meaningful summary."

    # Truncate very long text for the model
    if len(text) > 1000:
        text = text[:1000] + "..."

    try:
        start_time = time.time()
        summary = summarizer(text, max_length=150, min_length=100, do_sample=False)
        end_time = time.time()
        logger.info(f"Summary generated in {end_time - start_time:.2f} seconds")
        return summary[0]['summary_text']
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return f"Error generating summary: {str(e)}"
