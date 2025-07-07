from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import shutil
import os
import hashlib
import time
import logging
import state
from state import uploaded_file_path

from upload import generate_summary
from askanything import get_answer_with_justification, reset_document_index
from challenge import generate_questions_and_answers, evaluate_user_answers

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


summary_cache = {}
qa_cache = {}
challenge_cache = {}
file_hash_cache = {}
MAX_CACHE_SIZE = 100  

def get_file_hash(file_path):
    """Calculate MD5 hash of a file for caching"""
    try:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        return file_hash
    except Exception as e:
        logger.error(f"Error calculating file hash: {e}")
        return None

def get_question_hash(question):
    """Calculate hash of a question for caching"""
    return hashlib.md5(question.encode()).hexdigest()

def cleanup_cache(cache_dict, max_size=MAX_CACHE_SIZE):
    """Remove oldest entries from cache if it exceeds max size"""
    if len(cache_dict) > max_size:
        # Keep only the most recent entries
        items = list(cache_dict.items())
        cache_dict.clear()
        cache_dict.update(items[-max_size:])

def cleanup_all_caches():
    """Clean up all caches periodically"""
    cleanup_cache(summary_cache)
    cleanup_cache(qa_cache)
    cleanup_cache(challenge_cache)
    cleanup_cache(file_hash_cache)

app = FastAPI()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- ROUTES ---- #

UPLOAD_DIR = r"D:\GenAI\Backend\uploads"
@app.post("/upload/")
def upload_file(file: UploadFile = File(...)):
    start_time = time.time()
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    
    # Check if file already exists and is identical
    file_uploaded = False
    if os.path.exists(file_location):
        # Calculate hash of uploaded file
        file.file.seek(0)
        uploaded_content = file.file.read()
        uploaded_hash = hashlib.md5(uploaded_content).hexdigest()
        
        # Calculate hash of existing file
        existing_hash = get_file_hash(file_location)
        
        if uploaded_hash == existing_hash:
            logger.info(f"File {file.filename} already exists and is identical - skipping upload")
            file_uploaded = False
        else:
            # File is different, overwrite it
            file.file.seek(0)
            with open(file_location, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_uploaded = True
    else:
        # File doesn't exist, save it
        file.file.seek(0)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_uploaded = True

    # ✅ Save to global variable
    state.uploaded_file_path = file_location
    
    # Reset document index for new file (only if file was actually uploaded)
    if file_uploaded:
        reset_document_index()
        
        file_hash = get_file_hash(file_location)
        if file_hash:
            summary_cache.pop(file_hash, None)
            challenge_cache.pop(file_hash, None)
           
            qa_cache.clear()  
    
    
    if len(summary_cache) + len(qa_cache) + len(challenge_cache) > MAX_CACHE_SIZE * 2:
        cleanup_all_caches()
    
    end_time = time.time()
    logger.info(f"Upload processed in {end_time - start_time:.2f} seconds")
    
    return {"message": "File uploaded successfully", "path": file_location}

@app.get("/upload/")
def extract_text_api():
    start_time = time.time()
    
    # Check if file exists
    if not state.uploaded_file_path or not os.path.exists(state.uploaded_file_path):
        return {"summary": "No file uploaded yet."}
    
    # Get file hash for caching
    file_hash = get_file_hash(state.uploaded_file_path)
    if not file_hash:
        return {"summary": "Error processing file."}
    
    # Check cache first
    if file_hash in summary_cache:
        end_time = time.time()
        logger.info(f"Summary cache hit - returned in {end_time - start_time:.2f} seconds")
        return {"summary": summary_cache[file_hash]}
    
    # Generate summary and cache it
    summary = generate_summary()
    summary_cache[file_hash] = summary
    
    end_time = time.time()
    logger.info(f"Summary generated and cached in {end_time - start_time:.2f} seconds")
    
    return {"summary": summary}


class AskRequest(BaseModel):
    question: str

@app.post("/askanything/")
def ask_question(payload: AskRequest):
    start_time = time.time()
    
    # Check if file exists
    if not state.uploaded_file_path or not os.path.exists(state.uploaded_file_path):
        return {"question": payload.question, "answer": "Please upload a document first.", "justification": "No document available."}
    
    # Get file hash and question hash for caching
    file_hash = get_file_hash(state.uploaded_file_path)
    question_hash = get_question_hash(payload.question)
    cache_key = f"{file_hash}_{question_hash}"
    
    if not file_hash:
        return {"question": payload.question, "answer": "Error processing file.", "justification": "File processing error."}
    
    # Check cache first
    if cache_key in qa_cache:
        end_time = time.time()
        logger.info(f"Q&A cache hit - returned in {end_time - start_time:.2f} seconds")
        return qa_cache[cache_key]
    
    # Generate answer and cache it
    answer, justification = get_answer_with_justification(payload.question)
    result = {
        "question": payload.question,
        "answer": answer,
        "justification": justification
    }
    qa_cache[cache_key] = result
    
    end_time = time.time()
    logger.info(f"Q&A generated and cached in {end_time - start_time:.2f} seconds")
    
    return result



@app.get("/challenge/")
def get_generated_questions():
    start_time = time.time()
    
    # Check if file exists
    if not state.uploaded_file_path or not os.path.exists(state.uploaded_file_path):
        return {"questions": [{"question": "Please upload a document first."}]}
    
    # Get file hash for caching
    file_hash = get_file_hash(state.uploaded_file_path)
    if not file_hash:
        return {"questions": [{"question": "Error processing file."}]}
    
    # Check cache first
    if file_hash in challenge_cache:
        end_time = time.time()
        logger.info(f"Challenge cache hit - returned in {end_time - start_time:.2f} seconds")
        return {"questions": challenge_cache[file_hash]}
    
    # Generate questions and cache them
    questions = generate_questions_and_answers()
    challenge_cache[file_hash] = questions
    
    end_time = time.time()
    logger.info(f"Challenge questions generated and cached in {end_time - start_time:.2f} seconds")
    
    return {"questions": questions}


class ChallengeAnswer(BaseModel):
    user_answers: List[str]

@app.post("/challenge/")
def evaluate_answers(payload: ChallengeAnswer):
    results = evaluate_user_answers(payload.user_answers)
    return {"results": results}
