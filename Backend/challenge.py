from keybert import KeyBERT
from transformers import T5Tokenizer, T5ForConditionalGeneration
from sentence_transformers import SentenceTransformer, util
from upload import get_extracted_text


kw_model = None
qg_model = None
tokenizer = None
similarity_model = None

def initialize_models():
    """Initialize models with error handling"""
    global kw_model, qg_model, tokenizer, similarity_model
    
    try:
        if kw_model is None:
            print("Loading KeyBERT model...")
            kw_model = KeyBERT("all-MiniLM-L6-v2")
        
        if similarity_model is None:
            print("Loading SentenceTransformer model...")
            similarity_model = SentenceTransformer("all-MiniLM-L6-v2")
        
        if qg_model is None or tokenizer is None:
            print("Loading T5 question generation model...")
            tokenizer = T5Tokenizer.from_pretrained("mrm8488/t5-base-finetuned-question-generation-ap")
            qg_model = T5ForConditionalGeneration.from_pretrained("mrm8488/t5-base-finetuned-question-generation-ap")
        
        return True
    except Exception as e:
        print(f"Error initializing models: {e}")
        return False

# Global state for challenge
stored_challenge_qas = []

def generate_questions_and_answers():
    """Generate questions and answers from the uploaded document"""
    
    if not initialize_models():
        return [{"question": "Error: Could not initialize models. Please try again."}]
    
    context = get_extracted_text()
    
    # Check if document is available
    if context == "No file uploaded yet.":
        return [{"question": "Please upload a document first."}]
    
    # Check if context is too short
    if len(context.strip()) < 50:
        return [{"question": "Document is too short to generate meaningful questions."}]
    
    # Truncate context if too long for the model (T5 has 512 token limit)
    if len(context) > 2000:  # Rough estimate to stay under token limit
        context = context[:2000] + "..."
    
    try:
        # Extract key phrases with more diversity
        key_phrases = kw_model.extract_keywords(
            context, 
            keyphrase_ngram_range=(1, 3), 
            stop_words='english', 
            top_n=10,  
            diversity=0.7 
        )
        
        # Filter and diversify key phrases
        filtered_phrases = []
        seen_words = set()
        
        for phrase, score in key_phrases:
            if score > 0.3:  # Filter by relevance
                
                phrase_words = set(phrase.lower().split())
                if not phrase_words.intersection(seen_words) or len(filtered_phrases) < 2:
                    filtered_phrases.append(phrase)
                    seen_words.update(phrase_words)
                    
                    if len(filtered_phrases) >= 5:  # Limit to 5 diverse phrases
                        break
        
        if not filtered_phrases:
            return [{"question": "Could not extract meaningful topics from the document."}]
        
        questions = []
        global stored_challenge_qas
        stored_challenge_qas = []

        # Split context into different segments for variety
        context_segments = []
        sentences = context.split('.')
        segment_size = len(sentences) // 3
        
        for i in range(3):
            start_idx = i * segment_size
            end_idx = (i + 1) * segment_size if i < 2 else len(sentences)
            segment = '. '.join(sentences[start_idx:end_idx]).strip()
            if segment:
                context_segments.append(segment)
        
        # If we don't have enough segments, use the full context
        if len(context_segments) < 3:
            context_segments = [context[:800], context[400:1200], context[800:1600]]
        
        for i, phrase in enumerate(filtered_phrases[:3]):  # Use filtered phrases
            try:
                # Use different context segments and generation parameters for variety
                context_segment = context_segments[i % len(context_segments)]
                
                # Create input for question generation with varied context
                input_text = f"context: {context_segment[:800]} answer: {phrase}"
                input_ids = tokenizer.encode(input_text, return_tensors='pt', max_length=512, truncation=True)
                
                # Generate question with different parameters for variety
                generation_params = [
                    {"max_length": 64, "num_beams": 4, "do_sample": False, "temperature": 1.0},
                    {"max_length": 72, "num_beams": 3, "do_sample": True, "temperature": 0.8},
                    {"max_length": 56, "num_beams": 5, "do_sample": True, "temperature": 1.2}
                ]
                
                params = generation_params[i % len(generation_params)]
                
                with tokenizer.as_target_tokenizer():
                    output_ids = qg_model.generate(
                        input_ids, 
                        **params,
                        early_stopping=True,
                        pad_token_id=tokenizer.eos_token_id
                    )
                
                question = tokenizer.decode(output_ids[0], skip_special_tokens=True)
                
                # Clean up the question
                question = question.strip()
                if not question.endswith('?'):
                    question += '?'
                
                # Check for duplicate questions
                if question not in [q["question"] for q in questions]:
                    questions.append({"question": question})
                    stored_challenge_qas.append((question, phrase))
                else:
                    # Generate a fallback question if duplicate
                    fallback_question = generate_fallback_question(phrase, i)
                    questions.append({"question": fallback_question})
                    stored_challenge_qas.append((fallback_question, phrase))
                
            except Exception as e:
                print(f"Error generating question for phrase '{phrase}': {e}")
                # Generate a fallback question
                fallback_question = generate_fallback_question(phrase, i)
                questions.append({"question": fallback_question})
                stored_challenge_qas.append((fallback_question, phrase))
                continue
        
        # If T5 model failed, use simple question generation
        if not questions:
            print("T5 model failed, using simple question generation...")
            return generate_simple_questions(context, filtered_phrases)
        
        return questions
        
    except Exception as e:
        print(f"Error in generate_questions_and_answers: {e}")
        return [{"question": f"Error generating questions: {str(e)}"}]

def generate_simple_questions(context, key_phrases):
    """Fallback method to generate simple questions if T5 model fails"""
    questions = []
    global stored_challenge_qas
    stored_challenge_qas = []
    
    
    templates = [
        "What is {}?",
        "How would you define {}?",
        "Explain the concept of {}.",
        "What does {} mean in this context?",
        "Describe the role of {} in the document.",
        "What are the key characteristics of {}?",
        "How is {} relevant to the topic?",
        "What is the significance of {}?"
    ]
    
    
    for i, phrase in enumerate(key_phrases[:3]):
        template = templates[i * 2 % len(templates)]  # Skip templates for more variety
        question = template.format(phrase)
        questions.append({"question": question})
        stored_challenge_qas.append((question, phrase))
    
    return questions

def evaluate_user_answers(user_answers):
    """Evaluate user answers against expected answers"""
    if not initialize_models():
        return [{"question": "Error: Could not initialize models for evaluation.", "user_answer": "", "is_correct": False, "similarity": 0, "justification": "Model initialization failed"}]
    
    context = get_extracted_text()
    
    if context == "No file uploaded yet." or not stored_challenge_qas:
        return [{"question": "No questions available for evaluation.", "user_answer": "", "is_correct": False, "similarity": 0, "justification": "No document or questions available"}]
    
    results = []

    try:
        for user_ans, (question, expected_ans) in zip(user_answers, stored_challenge_qas):
            # Handle empty user answers
            if not user_ans or not user_ans.strip():
                results.append({
                    "question": question,
                    "expected_answer": expected_ans,
                    "user_answer": user_ans,
                    "is_correct": False,
                    "similarity": 0.0,
                    "justification": f"**❌ No answer provided.**\n**🎯 Expected answer:** {expected_ans}\n**💡 Hint:** Try to provide an answer based on the document content."
                })
                continue
            
            try:
                # Calculate similarity
                emb_user = similarity_model.encode(user_ans, convert_to_tensor=True)
                emb_exp = similarity_model.encode(expected_ans, convert_to_tensor=True)
                score = util.pytorch_cos_sim(emb_user, emb_exp).item()
                is_correct = score >= 0.6

                # Extract justification with improved method
                justification = extract_justification(context, expected_ans, user_ans, question)
                
                # Add score interpretation to justification
                score_interpretation = ""
                if score >= 0.8:
                    score_interpretation = "✅ Excellent match!"
                elif score >= 0.6:
                    score_interpretation = "👍 Good match!"
                elif score >= 0.4:
                    score_interpretation = "⚠️ Partial match."
                else:
                    score_interpretation = "❌ Poor match."
                
                justification += f"\n\n**🎯 Similarity Score:** {round(score, 2)} - {score_interpretation}"

                results.append({
                    "question": question,
                    "expected_answer": expected_ans,
                    "user_answer": user_ans,
                    "is_correct": is_correct,
                    "similarity": round(score, 2),
                    "justification": justification
                })
                
            except Exception as e:
                print(f"Error evaluating answer for question '{question}': {e}")
                # Still provide justification even if evaluation fails
                fallback_justification = f"**📝 Your answer:** {user_ans}\n**🎯 Expected answer:** {expected_ans}\n**⚠️ Error:** Evaluation failed: {str(e)}"
                results.append({
                    "question": question,
                    "expected_answer": expected_ans,
                    "user_answer": user_ans,
                    "is_correct": False,
                    "similarity": 0.0,
                    "justification": fallback_justification
                })

    except Exception as e:
        print(f"Error in evaluate_user_answers: {e}")
        return [{"question": "Error during evaluation", "user_answer": "", "is_correct": False, "similarity": 0, "justification": f"Evaluation error: {str(e)}"}]

    return results

def test_challenge_functionality():
    """Test function to debug challenge functionality"""
    print("Testing challenge functionality...")
    
    # Test model initialization
    if initialize_models():
        print("✅ Models initialized successfully")
    else:
        print("❌ Model initialization failed")
        return False
    
    # Test document extraction
    context = get_extracted_text()
    print(f"📄 Document length: {len(context)} characters")
    
    if context == "No file uploaded yet.":
        print("❌ No document uploaded")
        return False
    
    # Test keyword extraction
    try:
        key_phrases = kw_model.extract_keywords(context, keyphrase_ngram_range=(1, 3), stop_words='english', top_n=3)
        print(f"🔑 Key phrases extracted: {[phrase for phrase, score in key_phrases]}")
    except Exception as e:
        print(f"❌ Keyword extraction failed: {e}")
        return False
    
    print("✅ Challenge functionality test completed")
    return True

def extract_justification(context, expected_ans, user_ans, question):
    """Extract meaningful justification from the document context"""
    try:
        # Split context into sentences
        sentences = [s.strip() for s in context.split('.') if len(s.strip()) > 10]
        
        # Method 1: Look for sentences containing the expected answer
        relevant_sentences = []
        for sentence in sentences:
            if expected_ans.lower() in sentence.lower():
                relevant_sentences.append(sentence)
        
        # Method 2: If no direct match, look for sentences with similar keywords
        if not relevant_sentences:
            expected_keywords = set(expected_ans.lower().split())
            for sentence in sentences:
                sentence_words = set(sentence.lower().split())
                if len(expected_keywords.intersection(sentence_words)) >= 1:
                    relevant_sentences.append(sentence)
        
        # Method 3: Use semantic similarity to find relevant sentences
        if not relevant_sentences and similarity_model:
            sentence_embeddings = similarity_model.encode(sentences)
            expected_embedding = similarity_model.encode([expected_ans])
            
            # Calculate similarities
            similarities = util.pytorch_cos_sim(expected_embedding, sentence_embeddings)[0]
            
            # Get top 2 most similar sentences
            top_indices = similarities.argsort(descending=True)[:2]
            for idx in top_indices:
                if similarities[idx] > 0.3:  # Only if reasonably similar
                    relevant_sentences.append(sentences[idx])
        
        # Format the justification
        if relevant_sentences:
            # Take the best 1-2 sentences
            best_sentences = relevant_sentences[:2]
            justification = f"**📚 Context from document:**\n"
            for i, sentence in enumerate(best_sentences, 1):
                justification += f"{i}. {sentence.strip()}.\n"
            
            # Add expected answer context
            justification += f"\n**🎯 Expected answer:** {expected_ans}\n"
            justification += f"**📝 Your answer:** {user_ans}"
            
            return justification
        else:
            return f"**📝 Your answer:** {user_ans}\n**🎯 Expected answer:** {expected_ans}\n**ℹ️ Note:** Specific context not found in document, but answer is based on the document content."
    
    except Exception as e:
        return f"**📝 Your answer:** {user_ans}\n**🎯 Expected answer:** {expected_ans}\n**⚠️ Error:** Could not extract justification due to: {str(e)}"

def generate_fallback_question(phrase, index):
    """Generate a fallback question when T5 model fails or produces duplicates"""
    templates = [
        f"What is {phrase}?",
        f"How would you define {phrase}?",
        f"Explain the concept of {phrase}.",
        f"What does {phrase} refer to?",
        f"Describe {phrase} in your own words.",
        f"What is the significance of {phrase}?",
        f"How is {phrase} used in this context?",
        f"What are the key characteristics of {phrase}?"
    ]
    
    return templates[index % len(templates)]

# Uncomment the line below to test when the module is imported
# test_challenge_functionality()

def test_justification_extraction():
    """Test function to verify justification extraction works"""
    print("Testing justification extraction...")
    
    # Initialize models
    if not initialize_models():
        print("❌ Cannot test - models not initialized")
        return
    
    context = get_extracted_text()
    if context == "No file uploaded yet.":
        print("❌ Cannot test - no document uploaded")
        return
    
    # Test with sample data
    sample_expected_ans = "artificial intelligence"
    sample_user_ans = "AI technology"
    sample_question = "What is AI?"
    
    justification = extract_justification(context, sample_expected_ans, sample_user_ans, sample_question)
    print(f"✅ Justification extracted:\n{justification}")
    
    return True
