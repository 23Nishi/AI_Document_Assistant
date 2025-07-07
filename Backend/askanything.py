from upload import get_extracted_text 
from typing import List, Dict
import logging
import time
import os
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from transformers import pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load models once at module level
try:
    logger.info("Loading SentenceTransformer model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    logger.info("SentenceTransformer model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load SentenceTransformer model: {e}")
    model = None

try:
    logger.info("Loading QA pipeline...")
    qa_pipeline = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad")
    logger.info("QA pipeline loaded successfully")
except Exception as e:
    logger.error(f"Failed to load QA pipeline: {e}")
    qa_pipeline = None

# Cache for document embeddings and indices
document_cache = {}
MAX_CACHE_SIZE = 10

def get_document_cache_key():
    """Generate cache key for current document"""
    import state
    if not state.uploaded_file_path or not os.path.exists(state.uploaded_file_path):
        return None
    
    try:
        stat = os.stat(state.uploaded_file_path)
        return f"{state.uploaded_file_path}_{stat.st_mtime}_{stat.st_size}"
    except Exception as e:
        logger.error(f"Error getting document cache key: {e}")
        return None

def cleanup_document_cache():
    """Clean up old cache entries"""
    if len(document_cache) > MAX_CACHE_SIZE:
        
        items = list(document_cache.items())
        document_cache.clear()
        document_cache.update(items[-MAX_CACHE_SIZE:])

def parse_document_with_structure(text: str) -> List[Dict]:
    lines = text.split('\n')
    structured_chunks = []
    current_section = None
    paragraph_count = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if the line is a section header like "2.1 Methods"
        if line[0].isdigit() and '.' in line[:5]:
            current_section = line
            paragraph_count = 0
            continue
        
        # Otherwise, treat it as a paragraph
        paragraph_count += 1
        structured_chunks.append({
            "section": current_section,
            "paragraph_number": paragraph_count,
            "text": line
        })
    
    return structured_chunks
# Initialize global variables (legacy compatibility)
structured_chunks = []
index = None

def initialize_document_index():
    """Initialize the document index when a file is uploaded"""
    global structured_chunks, index
    
    if not model:
        logger.error("SentenceTransformer model not available")
        return False
    
    
    cache_key = get_document_cache_key()
    if not cache_key:
        return False
    
    
    if cache_key in document_cache:
        logger.info("Document index cache hit")
        cached_data = document_cache[cache_key]
        structured_chunks = cached_data["structured_chunks"]
        index = cached_data["index"]
        return True
    
    
    start_time = time.time()
    document_text = get_extracted_text()
    if document_text == "No file uploaded yet." or document_text.startswith("Error"):
        return False
    
    structured_chunks = parse_document_with_structure(document_text)
    texts = [chunk["text"] for chunk in structured_chunks]
    
    if not texts:
        return False
    
    try:
        # Create embeddings
        embeddings = model.encode(texts)
        index = faiss.IndexFlatL2(embeddings[0].shape[0])
        index.add(np.array(embeddings))
        
        # Cache the results
        document_cache[cache_key] = {
            "structured_chunks": structured_chunks,
            "index": index
        }
        cleanup_document_cache()
        
        end_time = time.time()
        logger.info(f"Document index created and cached in {end_time - start_time:.2f} seconds")
        return True
        
    except Exception as e:
        logger.error(f"Error creating document index: {e}")
        return False

def reset_document_index():
    """Reset the document index when a new file is uploaded"""
    global structured_chunks, index
    structured_chunks = []
    index = None


from transformers import pipeline

qa_pipeline = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad")

def get_answer_with_justification(question: str, k=3):
    
    if index is None:
        if not initialize_document_index():
            return "Please upload a document first.", "No document available for processing."
    
    # Encode question and retrieve top-k chunks using FAISS
    q_embedding = model.encode([question])
    _, indices = index.search(np.array(q_embedding), k)

    # Combine top-k chunk texts into a single context string
    combined_context = "\n".join([structured_chunks[i]['text'] for i in indices[0]])

    
    result = qa_pipeline(question=question, context=combined_context)
    best_answer = result['answer']

    # Use the top-1 chunk for justification metadata
    top_index = indices[0][0]
    best_chunk = structured_chunks[top_index]

    justification = (
        f"📌 **Justification:**\n"
        f"- 🔢 Paragraph Number: {best_chunk['paragraph_number']}\n"
        f"- 📚 Section: {best_chunk['section']}\n"
        f"- 📄 Context used:\n\n{combined_context.strip()}"
    )

    return best_answer, justification



