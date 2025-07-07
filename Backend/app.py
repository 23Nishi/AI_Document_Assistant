import streamlit as st
import requests
import os
import time

API_URL = "http://localhost:8000"  # FastAPI backend base URL

# Configure page
st.set_page_config(
    page_title="AI Document Assistant", 
    layout="wide",
    page_icon="🧠",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .section-header {
        background: linear-gradient(135deg, #334155 0%, #475569 100%);
        color: white;
        padding: 1.2rem;
        border-radius: 10px;
        margin: 1.5rem 0;
        text-align: center;
        font-weight: 600;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .upload-zone {
        border: 2px dashed #475569;
        border-radius: 12px;
        padding: 2.5rem;
        text-align: center;
        background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%);
        margin: 1rem 0;
        color: #1e293b;
        font-weight: 500;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    }
    
    .upload-zone h3 {
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    
    .upload-zone p {
        color: #475569;
    }
    
    .success-box {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        color: white;
        padding: 1.2rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.1);
        font-weight: 500;
    }
    
    .question-box {
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
        padding: 1.8rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        border: 1px solid #cbd5e1;
        color: #1e293b;
    }
    
    .question-box h4 {
        color: #1e293b;
        margin-bottom: 0.8rem;
    }
    
    .answer-box {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        padding: 1.8rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 4px solid #1e3c72;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        color: #1e293b;
        border: 1px solid #e2e8f0;
    }
    
    .answer-box h4 {
        color: #1e293b;
        margin-bottom: 0.8rem;
    }
    
    .challenge-box {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        padding: 1.8rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        border: 1px solid #93c5fd;
        color: #1e40af;
    }
    
    .challenge-box h4 {
        color: #1e40af;
        margin-bottom: 0.5rem;
    }
    
    .challenge-box p {
        color: #3730a3;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.7rem 2.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(30, 60, 114, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(30, 60, 114, 0.4);
        background: linear-gradient(135deg, #1e40af 0%, #3730a3 100%);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        padding: 1.2rem;
        border-radius: 10px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        text-align: center;
        margin: 0.5rem;
        border: 1px solid #e2e8f0;
    }
    
    .error-box {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 4px 16px rgba(220, 38, 38, 0.2);
        font-weight: 500;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 4px 16px rgba(217, 119, 6, 0.2);
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


st.markdown("""
<div class="main-header">
    <h1>📊 Document Assistant</h1>
    <p>Advanced AI-Powered Document Analysis & Knowledge Assessment Platform</p>
</div>
""", unsafe_allow_html=True)


with st.sidebar:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #334155 0%, #475569 100%); color: white; padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);">
        <h3>📚 User Guide</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    **Step 1:** 📤 Upload your PDF or TXT document
    
    **Step 2:** ❓ Ask detailed questions about your document
    
    **Step 3:** 🎯 Test your knowledge with AI-generated assessments
    """)
    
    st.markdown("---")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #475569 0%, #64748b 100%); color: white; padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);">
        <h4>💡 Best Practices</h4>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    • Use specific and detailed questions for accurate answers
    • Try various question formats (analytical, factual, conceptual)
    • Upload well-structured documents for optimal results
    • Review AI justifications to understand reasoning
    """)
    
    st.markdown("---")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);">
        <h4>⚡ Platform Features</h4>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    ✅ **Intelligent Caching** - Optimized response times for repeated queries
    
    ✅ **Auto-Summarization** - AI-generated document summaries
    
    ✅ **Contextual Analysis** - Source-referenced answer generation
    
    ✅ **Knowledge Assessment** - Automated question generation and evaluation
    
    ✅ **Performance Analytics** - Real-time metrics and accuracy tracking
    """)
    
    st.markdown("---")
    
    # Add some metrics if document is uploaded
    if 'questions' in st.session_state:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #64748b 0%, #94a3b8 100%); color: white; padding: 1.2rem; border-radius: 10px; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);">
            <h4>📊 Session Analytics</h4>
        </div>
        """, unsafe_allow_html=True)
        
        st.metric("Questions Generated", len(st.session_state.questions))
        if hasattr(st.session_state, 'user_answers'):
            answered = sum(1 for ans in st.session_state.user_answers if ans.strip())
            st.metric("Questions Answered", answered)

# --- Upload Section ---
st.markdown("""
<div class="section-header">
    📤  Document Upload & Processing
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
    <div class="upload-zone">
        <h3>📄 Secure Document Upload Center</h3>
        <p>Accepts PDF and TXT file formats for analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Select your document for analysis", 
        type=["pdf", "txt"],
        help="Upload a PDF or TXT file to begin comprehensive AI analysis"
    )

if uploaded_file is not None:
    with st.spinner("⚙️ Processing document and initializing AI analysis..."):
        # Save the uploaded file to a fixed path
        UPLOAD_DIR = r"D:\GenAI\Backend\uploads"
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)

        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())

        # Upload to FastAPI backend
        with open(file_path, "rb") as f:
            response = requests.post(f"{API_URL}/upload/", files={"file": f})

    if response.status_code == 200:
        st.markdown("""
        <div class="success-box">
            ✅ Document uploaded and processed successfully
        </div>
        """, unsafe_allow_html=True)

        # Extract summary after upload
        with st.spinner("🤖 Generating comprehensive AI summary..."):
            extract_res = requests.get(f"{API_URL}/upload/")
            
        if extract_res.status_code == 200:
            summary_data = extract_res.json()
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    label="📊 Status", 
                    value="✅ Ready", 
                    help="Document is processed and ready for questions"
                )
            with col2:
                st.metric(
                    label="📝 File Type", 
                    value=uploaded_file.name.split('.')[-1].upper(),
                    help="Type of uploaded document"
                )
            with col3:
                st.metric(
                    label="📏 File Size", 
                    value=f"{uploaded_file.size // 1024} KB",
                    help="Size of uploaded document"
                )
            
            st.markdown("### 📋 Executive Summary")
            st.markdown(f"""
            <div class="answer-box">
                <p>{summary_data['summary']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="error-box">
                ❌ Document processing failed. Please try again.
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="error-box">
            ❌ Upload failed. Please check your file and try again.
        </div>
        """, unsafe_allow_html=True)


st.markdown("""
<hr style="border: none; height: 2px; background: linear-gradient(90deg, #334155 0%, #475569 100%); margin: 3rem 0;">
""", unsafe_allow_html=True)


# --- Ask Anything Section ---
st.markdown("""
<div class="section-header">
    ❓ Ask  Anything
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col1:
    question = st.text_input(
        "💭 Enter your analytical question:",
        placeholder="Type your question here... (e.g., What are the key findings of this document?)",
        help="Ask detailed questions to receive comprehensive AI-powered analysis"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)  # Add space
    ask_button = st.button("� Analyze Query", use_container_width=True)

if ask_button:
    if not question:
        st.markdown("""
        <div class="warning-box">
            ⚠️ Please enter a question to proceed with analysis.
        </div>
        """, unsafe_allow_html=True)
    else:
        with st.spinner("� AI is analyzing your query..."):
            start_time = time.time()
            res = requests.post(f"{API_URL}/askanything/", json={"question": question})
            end_time = time.time()
            
        if res.status_code == 200:
            data = res.json()
            
            st.markdown(f"""
            <div class="question-box">
                <h4>❓ Query Submitted:</h4>
                <p><em>"{question}"</em></p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="answer-box">
                <h4>🧠 AI Analysis Result:</h4>
                <p>{data['answer']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            
            with st.expander("📌 View Detailed Analysis & Source References", expanded=False):
                st.markdown(data['justification'])
                
        else:
            st.markdown("""
            <div class="error-box">
                ❌ Analysis failed. Please try again.
            </div>
            """, unsafe_allow_html=True)


st.markdown("""
<hr style="border: none; height: 2px; background: linear-gradient(90deg, #334155 0%, #475569 100%); margin: 3rem 0;">
""", unsafe_allow_html=True)

# --- Challenge Me Section ---
st.markdown("""
<div class="section-header">
    🎯 Challenge Me
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="challenge-box">
    <h4>📊 Ready for Knowledge Assessment?</h4>
    <p>Test your comprehension with AI-generated questions based on document analysis</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    generate_button = st.button("📋 Generate Assessment", use_container_width=True)

if generate_button:
    with st.spinner("🤖 Generating personalized assessment questions..."):
        start_time = time.time()
        response = requests.get(f"{API_URL}/challenge/")
        end_time = time.time()
        
    if response.status_code == 200:
        st.session_state.questions = response.json()["questions"]
        st.session_state.user_answers = [""] * len(st.session_state.questions)
        
        st.markdown("""
        <div class="success-box">
            ✅ Assessment questions generated successfully
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="error-box">
            ❌ Failed to generate assessment questions. Please try again.
        </div>
        """, unsafe_allow_html=True)

if "questions" in st.session_state:
    st.markdown("### 📝 Complete the Assessment")
    
    for idx, qa in enumerate(st.session_state.questions):
        st.markdown(f"""
        <div class="question-box">
            <h4>Question {idx + 1}:</h4>
            <p>{qa['question']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.session_state.user_answers[idx] = st.text_area(
            label=f"Your Response for Question {idx + 1}:",
            key=f"user_answer_{idx}",
            placeholder="Enter your detailed response here...",
            height=100
        )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        submit_button = st.button("📊 Submit for Evaluation", use_container_width=True)

    if submit_button:
        with st.spinner("🔍 Evaluating your responses..."):
            payload = {"user_answers": st.session_state.user_answers}
            eval_res = requests.post(f"{API_URL}/challenge/", json=payload)
            
        if eval_res.status_code == 200:
            results = eval_res.json()["results"]
            
            # Calculate overall score
            correct_answers = sum(1 for r in results if r['is_correct'])
            total_questions = len(results)
            score_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
            
            # Display overall score
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    label="🎯 Score", 
                    value=f"{correct_answers}/{total_questions}",
                    help="Number of correct responses"
                )
            with col2:
                st.metric(
                    label="📊 Accuracy", 
                    value=f"{score_percentage:.1f}%",
                    help="Overall accuracy percentage"
                )
            with col3:
                if score_percentage >= 80:
                    performance = "🌟 Excellent"
                elif score_percentage >= 60:
                    performance = "👍 Good"
                elif score_percentage >= 40:
                    performance = "⚠️ Fair"
                else:
                    performance = "📚 Needs Improvement"
                
                st.metric(
                    label="🏆 Performance", 
                    value=performance,
                    help="Overall performance assessment"
                )
            
            st.markdown("### 📋 Detailed Evaluation Results")
            
            for idx, r in enumerate(results):
                
                if r['is_correct']:
                    box_style = "background: linear-gradient(135deg, #059669 0%, #047857 100%); color: white;"
                    icon = "✅"
                else:
                    box_style = "background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color: white;"
                    icon = "❌"
                
                st.markdown(f"""
                <div style="{box_style} padding: 1.5rem; border-radius: 10px; margin: 1rem 0; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);">
                    <h4>{icon} Question {idx + 1}: {r['question']}</h4>
                    <p><strong>Your Response:</strong> <code>{r['user_answer']}</code></p>
                    <p><strong>Similarity Score:</strong> {r['similarity']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                
                with st.expander(f"📌 View Detailed Explanation for Question {idx + 1}", expanded=False):
                    st.markdown(r['justification'])
                
        else:
            st.markdown("""
            <div class="error-box">
                ❌ Evaluation failed. Please try again.
            </div>
            """, unsafe_allow_html=True)

