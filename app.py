
import streamlit as st
import os
import numpy as np
import faiss

from groq import Groq
from pypdf import PdfReader
from docx import Document
from sentence_transformers import SentenceTransformer


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI WorkMate",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

    /* Main App Background */
    .stApp {
        background: linear-gradient(
            135deg,
            #eef2ff 0%,
            #f8f9ff 45%,
            #ecfeff 100%
        );
    }

    /* Main content */
    .main {
        padding: 1rem 2rem;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(
            180deg,
            #172554 0%,
            #312e81 50%,
            #4c1d95 100%
        );
    }

    section[data-testid="stSidebar"] * {
        color: white !important;
    }

    /* Main title */
    .main-title {
        font-size: 48px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 5px;

        background: linear-gradient(
            90deg,
            #2563eb,
            #7c3aed,
            #db2777
        );

        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Subtitle */
    .subtitle {
        text-align: center;
        font-size: 19px;
        color: #475569;
        margin-bottom: 30px;
    }

    /* Feature cards */
    .feature-card {
        background: rgba(255,255,255,0.90);
        padding: 25px;
        border-radius: 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 8px 25px rgba(15,23,42,0.08);
        margin-bottom: 20px;
        min-height: 145px;
        transition: 0.3s;
    }

    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 15px 35px rgba(15,23,42,0.13);
    }

    .feature-icon {
        font-size: 35px;
    }

    .feature-title {
        font-size: 20px;
        font-weight: 700;
        color: #172554;
        margin-top: 8px;
    }

    .feature-description {
        font-size: 14px;
        color: #64748b;
    }

    /* AI response box */
    .response-box {
        background: white;
        padding: 25px;
        border-radius: 18px;
        border-left: 6px solid #6366f1;
        box-shadow: 0 8px 25px rgba(15,23,42,0.08);
        margin-top: 20px;
    }

    /* Section headings */
    .section-title {
        color: #312e81;
        font-size: 30px;
        font-weight: 750;
        margin-top: 20px;
    }

    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        border: none;
        padding: 12px 20px;
        font-weight: 700;

        background: linear-gradient(
            90deg,
            #2563eb,
            #7c3aed
        );

        color: white;
        transition: 0.3s;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(79,70,229,0.30);
    }

    /* Text areas and inputs */
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox div {
        border-radius: 12px !important;
    }

    /* Upload box */
    [data-testid="stFileUploader"] {
        background: rgba(255,255,255,0.75);
        border-radius: 15px;
        padding: 10px;
        border: 1px dashed #6366f1;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #64748b;
        padding: 30px;
        margin-top: 40px;
    }

</style>
""", unsafe_allow_html=True)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">🤖 AI WorkMate</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Your Smart AI Assistant for Online Work, Freelancing & Career'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# API KEY
# =========================================================

st.sidebar.markdown("## 🔐 AI Configuration")

api_key = st.sidebar.text_input(
    "Groq API Key",
    type="password",
    placeholder="Enter your API key"
)

if not api_key:
    st.sidebar.info(
        "Enter your Groq API key to activate AI features."
    )
    st.stop()

client = Groq(api_key=api_key)


# =========================================================
# AI FUNCTION
# =========================================================

def ask_ai(prompt):

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": """
You are AI WorkMate.

You help users with:
- Freelancing
- Online work
- Job applications
- Professional communication
- Resume improvement
- Documents
- Writing

Give clear, useful and professional answers.
Never invent personal information or experience.
"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4
    )

    return response.choices[0].message.content


# =========================================================
# DOCUMENT FUNCTIONS
# =========================================================

def extract_pdf(file):

    reader = PdfReader(file)

    text = ""

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        page_text = page.extract_text() or ""

        text += (
            f"\n[Page {page_number}]\n"
            f"{page_text}"
        )

    return text


def extract_docx(file):

    document = Document(file)

    text = ""

    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"

    return text


def extract_txt(file):

    return file.read().decode(
        "utf-8",
        errors="ignore"
    )


def extract_document(file):

    name = file.name.lower()

    if name.endswith(".pdf"):
        return extract_pdf(file)

    elif name.endswith(".docx"):
        return extract_docx(file)

    elif name.endswith(".txt"):
        return extract_txt(file)

    return ""


# =========================================================
# CHUNKING
# =========================================================

def create_chunks(
    text,
    chunk_size=1000,
    overlap=150
):

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


# =========================================================
# SIDEBAR MENU
# =========================================================

st.sidebar.markdown("---")

st.sidebar.markdown("## 🛠️ AI Tools")

tool = st.sidebar.radio(
    "Choose a tool",
    [
        "🏠 Home",
        "🤖 AI Work Assistant",
        "💼 Proposal Generator",
        "📧 Email Generator",
        "📄 Resume Analyzer",
        "🔎 Job Description Analyzer",
        "📚 Document Assistant",
        "📝 AI Summarizer",
        "✍️ Text Rewriter"
    ]
)


# =========================================================
# HOME
# =========================================================

if tool == "🏠 Home":

    st.markdown(
        '<div class="section-title">'
        '✨ Everything You Need for Online Work'
        '</div>',
        unsafe_allow_html=True
    )

    st.write(
        "AI WorkMate combines multiple AI tools "
        "into one simple and professional workspace."
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Row 1
    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🤖</div>
            <div class="feature-title">
                AI Work Assistant
            </div>
            <div class="feature-description">
                Get AI help with your daily online work.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:

        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">💼</div>
            <div class="feature-title">
                Proposal Generator
            </div>
            <div class="feature-description">
                Create professional freelancing proposals.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:

        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📧</div>
            <div class="feature-title">
                Email Generator
            </div>
            <div class="feature-description">
                Write professional emails quickly.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Row 2
    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📄</div>
            <div class="feature-title">
                Resume Analyzer
            </div>
            <div class="feature-description">
                Analyze your resume against a job.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:

        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🔎</div>
            <div class="feature-title">
                Job Analyzer
            </div>
            <div class="feature-description">
                Extract skills and requirements from jobs.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:

        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📚</div>
            <div class="feature-title">
                Document Assistant
            </div>
            <div class="feature-description">
                Ask questions from your documents using RAG.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.info(
        "💡 Select any AI tool from the sidebar to get started."
    )


# =========================================================
# AI WORK ASSISTANT
# =========================================================

elif tool == "🤖 AI Work Assistant":

    st.markdown(
        '<div class="section-title">'
        '🤖 AI Work Assistant'
        '</div>',
        unsafe_allow_html=True
    )

    task = st.text_area(
        "What do you need help with?",
        height=180,
        placeholder=(
            "Example: Help me write a professional "
            "message to a client."
        )
    )

    if st.button("✨ Generate Answer"):

        if task.strip():

            with st.spinner("AI is working..."):

                result = ask_ai(task)

            st.markdown(
                '<div class="response-box">',
                unsafe_allow_html=True
            )

            st.markdown(result)

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )

        else:

            st.warning(
                "Please enter your task."
            )


# =========================================================
# PROPOSAL GENERATOR
# =========================================================

elif tool == "💼 Proposal Generator":

    st.markdown(
        '<div class="section-title">'
        '💼 Freelancing Proposal Generator'
        '</div>',
        unsafe_allow_html=True
    )

    job = st.text_area(
        "📌 Job Description",
        height=220,
        placeholder="Paste the client's job description..."
    )

    skills = st.text_input(
        "🛠️ Your Skills",
        placeholder="Python, AI, Streamlit, RAG"
    )

    experience = st.text_area(
        "📚 Your Experience"
    )

    tone = st.selectbox(
        "🎨 Proposal Tone",
        [
            "Professional",
            "Friendly",
            "Short & Direct"
        ]
    )

    if st.button("🚀 Generate Proposal"):

        if job.strip():

            prompt = f"""
Create a professional freelancing proposal.

Job:
{job}

Skills:
{skills}

Experience:
{experience}

Tone:
{tone}

Rules:
- Focus on the client's needs.
- Keep it natural.
- Do not make false claims.
"""

            with st.spinner(
                "Creating your proposal..."
            ):

                result = ask_ai(prompt)

            st.markdown(
                '<div class="response-box">',
                unsafe_allow_html=True
            )

            st.markdown(result)

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )

        else:

            st.warning(
                "Please enter the job description."
            )


# =========================================================
# EMAIL GENERATOR
# =========================================================

elif tool == "📧 Email Generator":

    st.markdown(
        '<div class="section-title">'
        '📧 AI Email Generator'
        '</div>',
        unsafe_allow_html=True
    )

    recipient = st.text_input(
        "👤 Recipient"
    )

    purpose = st.text_area(
        "📝 Email Purpose",
        height=180,
        placeholder=(
            "Example: Follow up with a client "
            "who has not replied."
        )
    )

    tone = st.selectbox(
        "🎨 Email Tone",
        [
            "Professional",
            "Friendly",
            "Formal",
            "Short"
        ]
    )

    if st.button("✉️ Generate Email"):

        if purpose.strip():

            prompt = f"""
Write a professional email.

Recipient:
{recipient}

Purpose:
{purpose}

Tone:
{tone}

Include:
- Subject
- Greeting
- Main message
- Closing

Do not invent information.
"""

            with st.spinner(
                "Writing your email..."
            ):

                result = ask_ai(prompt)

            st.markdown(
                '<div class="response-box">',
                unsafe_allow_html=True
            )

            st.markdown(result)

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )

        else:

            st.warning(
                "Please enter the email purpose."
            )


# =========================================================
# RESUME ANALYZER
# =========================================================

elif tool == "📄 Resume Analyzer":

    st.markdown(
        '<div class="section-title">'
        '📄 AI Resume Analyzer'
        '</div>',
        unsafe_allow_html=True
    )

    resume = st.file_uploader(
        "📤 Upload Resume",
        type=["pdf", "docx", "txt"]
    )

    job = st.text_area(
        "📌 Paste Job Description",
        height=220
    )

    if st.button("🔍 Analyze Resume"):

        if resume and job.strip():

            resume_text = extract_document(
                resume
            )

            prompt = f"""
Analyze this resume against the job description.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job}

Provide:

1. Overall match percentage
2. Matching skills
3. Missing skills
4. ATS keywords
5. Resume problems
6. Improvement suggestions
7. Recommended changes

Do not invent information.
"""

            with st.spinner(
                "Analyzing resume..."
            ):

                result = ask_ai(prompt)

            st.markdown(
                '<div class="response-box">',
                unsafe_allow_html=True
            )

            st.markdown(result)

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )

        else:

            st.warning(
                "Upload a resume and enter a job description."
            )


# =========================================================
# JOB DESCRIPTION ANALYZER
# =========================================================

elif tool == "🔎 Job Description Analyzer":

    st.markdown(
        '<div class="section-title">'
        '🔎 Job Description Analyzer'
        '</div>',
        unsafe_allow_html=True
    )

    job = st.text_area(
        "📌 Paste Job Description",
        height=300
    )

    if st.button("🔍 Analyze Job"):

        if job.strip():

            prompt = f"""
Analyze this job description:

{job}

Extract:

1. Job title
2. Required skills
3. Preferred skills
4. Experience requirements
5. Education requirements
6. Technologies
7. ATS keywords
8. Main responsibilities
9. Important requirements
"""

            with st.spinner(
                "Analyzing job..."
            ):

                result = ask_ai(prompt)

            st.markdown(
                '<div class="response-box">',
                unsafe_allow_html=True
            )

            st.markdown(result)

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )

        else:

            st.warning(
                "Please enter a job description."
            )


# =========================================================
# DOCUMENT ASSISTANT
# =========================================================

elif tool == "📚 Document Assistant":

    st.markdown(
        '<div class="section-title">'
        '📚 AI Document Assistant'
        '</div>',
        unsafe_allow_html=True
    )

    uploaded_file = st.file_uploader(
        "📤 Upload Document",
        type=["pdf", "docx", "txt"]
    )

    if uploaded_file:

        document_text = extract_document(
            uploaded_file
        )

        st.success(
            f"✅ Loaded: {uploaded_file.name}"
        )

        st.metric(
            "Characters Extracted",
            len(document_text)
        )

        chunks = create_chunks(
            document_text
        )

        st.metric(
            "Document Chunks",
            len(chunks)
        )

        question = st.text_input(
            "💬 Ask a question about your document"
        )

        if st.button("🔎 Search Document"):

            if question.strip():

                with st.spinner(
                    "Creating embeddings..."
                ):

                    model = SentenceTransformer(
                        "all-MiniLM-L6-v2"
                    )

                    embeddings = model.encode(
                        chunks
                    )

                    embeddings = np.array(
                        embeddings
                    ).astype("float32")

                    index = faiss.IndexFlatL2(
                        embeddings.shape[1]
                    )

                    index.add(embeddings)

                    question_embedding = model.encode(
                        [question]
                    )

                    question_embedding = np.array(
                        question_embedding
                    ).astype("float32")

                    distances, indices = index.search(
                        question_embedding,
                        min(3, len(chunks))
                    )

                    relevant_chunks = [
                        chunks[i]
                        for i in indices[0]
                    ]

                    context = "\n\n".join(
                        relevant_chunks
                    )

                prompt = f"""
Answer the question using ONLY
the document context.

DOCUMENT:
{context}

QUESTION:
{question}

If the answer is not present,
say that it was not found in the document.
"""

                with st.spinner(
                    "Generating answer..."
                ):

                    result = ask_ai(prompt)

                st.markdown(
                    '<div class="response-box">',
                    unsafe_allow_html=True
                )

                st.markdown(result)

                st.markdown(
                    '</div>',
                    unsafe_allow_html=True
                )

            else:

                st.warning(
                    "Please enter a question."
                )


# =========================================================
# SUMMARIZER
# =========================================================

elif tool == "📝 AI Summarizer":

    st.markdown(
        '<div class="section-title">'
        '📝 AI Summarizer'
        '</div>',
        unsafe_allow_html=True
    )

    text = st.text_area(
        "Enter text",
        height=300
    )

    length = st.selectbox(
        "Summary Length",
        [
            "Short",
            "Medium",
            "Detailed"
        ]
    )

    if st.button("✨ Create Summary"):

        if text.strip():

            prompt = f"""
Summarize the following text.

Length:
{length}

Text:
{text}

Keep the important information.
"""

            with st.spinner(
                "Creating summary..."
            ):

                result = ask_ai(prompt)

            st.markdown(
                '<div class="response-box">',
                unsafe_allow_html=True
            )

            st.markdown(result)

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )

        else:

            st.warning(
                "Please enter some text."
            )


# =========================================================
# TEXT REWRITER
# =========================================================

elif tool == "✍️ Text Rewriter":

    st.markdown(
        '<div class="section-title">'
        '✍️ AI Text Rewriter'
        '</div>',
        unsafe_allow_html=True
    )

    text = st.text_area(
        "Enter your text",
        height=250
    )

    style = st.selectbox(
        "🎨 Rewrite Style",
        [
            "Professional",
            "Simple",
            "Friendly",
            "Formal",
            "Concise"
        ]
    )

    if st.button("✨ Rewrite Text"):

        if text.strip():

            prompt = f"""
Rewrite this text.

Style:
{style}

Original text:
{text}

Keep the original meaning.
Do not add false information.
"""

            with st.spinner(
                "Rewriting..."
            ):

                result = ask_ai(prompt)

            st.markdown(
                '<div class="response-box">',
                unsafe_allow_html=True
            )

            st.markdown(result)

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )

        else:

            st.warning(
                "Please enter some text."
            )


# =========================================================
# FOOTER
# =========================================================

st.markdown("""
<div class="footer">
    🤖 <b>AI WorkMate</b> — Work Smarter with AI
    <br>
    Built with Python, Streamlit, RAG & AI
</div>
""", unsafe_allow_html=True)
```

### `requirements.txt`

:::writing{variant="document" id="74106" title="requirements.txt"}
```text
streamlit
groq
pypdf
python-docx
sentence-transformers
faiss-cpu
numpy
```

### 🎨 اس version میں کیا نیا ہے؟

آپ کی app اب سادہ Streamlit app نہیں لگے گی بلکہ اس میں:

- 🌈 Gradient background
- 💙 Professional blue/purple theme
- 🟪 Colourful sidebar
- 🧩 Modern feature cards
- ✨ Gradient buttons
- 📱 Responsive layout
- 🤖 Professional AI header
- 📄 Modern upload area
- 💬 Styled AI response boxes
- 🏠 Proper Home Dashboard
- 🎯 Icons اور visual sections

شامل ہیں۔

**اہم:** اگر آپ اسے public website پر deploy کریں تو Groq API key کو sidebar میں user سے لینے کے بجائے **Streamlit Secrets** میں رکھنا بہتر ہوگا۔
