import io

import numpy as np
import streamlit as st
from docx import Document
from groq import Groq
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

MODEL = "openai/gpt-oss-120b"
MAX_CHARS = 12000  # keeps prompts inside the model's limits

st.set_page_config(
    page_title="AI WorkMate",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# CUSTOM CSS (colorful theme)
# =========================================================
st.markdown(
    """
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #eef2ff 0%, #f8f9ff 45%, #ecfeff 100%);
    }

    /* Sidebar background */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #172554 0%, #312e81 50%, #4c1d95 100%);
    }

    /* Sidebar text: white, but NOT inside inputs or alert boxes */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown p {
        color: white !important;
    }
    section[data-testid="stSidebar"] [data-testid="stAlert"] p {
        color: #1e3a8a !important;
    }
    section[data-testid="stSidebar"] input {
        color: #0f172a !important;
    }

    /* Title */
    .main-title {
        font-size: 48px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 5px;
        background: linear-gradient(90deg, #2563eb, #7c3aed, #db2777);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .subtitle {
        text-align: center;
        font-size: 19px;
        color: #475569;
        margin-bottom: 30px;
    }

    /* Section headings */
    .section-title {
        color: #312e81;
        font-size: 30px;
        font-weight: 750;
        margin: 10px 0 15px 0;
    }

    /* Home feature cards */
    .feature-card {
        background: rgba(255,255,255,0.92);
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
    .feature-icon { font-size: 35px; }
    .feature-title {
        font-size: 20px;
        font-weight: 700;
        color: #172554;
        margin-top: 8px;
    }
    .feature-description { font-size: 14px; color: #64748b; }

    /* AI response box (st.container(border=True)) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: white;
        border-radius: 18px;
        border: 1px solid #e2e8f0;
        border-left: 6px solid #6366f1;
        box-shadow: 0 8px 25px rgba(15,23,42,0.08);
        padding: 8px 12px;
        margin-top: 15px;
    }

    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        border: none;
        padding: 12px 20px;
        font-weight: 700;
        background: linear-gradient(90deg, #2563eb, #7c3aed);
        color: white;
        transition: 0.3s;
    }
    .stButton > button:hover {
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(79,70,229,0.30);
    }

    /* Inputs */
    .stTextInput input, .stTextArea textarea {
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
""",
    unsafe_allow_html=True,
)

# =========================================================
# HEADER
# =========================================================
st.markdown('<div class="main-title">🤖 AI WorkMate</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Your Smart AI Assistant for Online Work, Freelancing & Career</div>',
    unsafe_allow_html=True,
)

# =========================================================
# API KEY (Streamlit secrets first, sidebar input as fallback)
# =========================================================
st.sidebar.markdown("## 🔐 AI Configuration")


def get_api_key():
    try:
        key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        key = ""
    if key:
        return key
    return st.sidebar.text_input(
        "Groq API Key", type="password", placeholder="Enter your API key"
    )


api_key = get_api_key()
if not api_key:
    st.sidebar.info("Enter your Groq API key to activate AI features.")
    st.stop()

client = Groq(api_key=api_key)

SYSTEM_PROMPT = """You are AI WorkMate.
You help users with freelancing, online work, job applications, professional
communication, resume improvement, documents and writing.
Give clear, useful and professional answers.
Never invent personal information or experience."""


# =========================================================
# HELPERS
# =========================================================
def ask_ai(prompt):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
    )
    return response.choices[0].message.content


def run(prompt):
    """Call the AI, handle errors, show the answer in the styled box."""
    with st.spinner("AI is working..."):
        try:
            answer = ask_ai(prompt)
        except Exception as e:
            st.error(f"AI request failed: {e}")
            return
    with st.container(border=True):
        st.markdown(answer)


def section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


def clip(text):
    return text[:MAX_CHARS]


def read_file(file):
    data = file.getvalue()
    name = file.name.lower()
    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(
            f"[Page {i}]\n{page.extract_text() or ''}"
            for i, page in enumerate(reader.pages, start=1)
        )
    if name.endswith(".docx"):
        return "\n".join(p.text for p in Document(io.BytesIO(data)).paragraphs)
    return data.decode("utf-8", errors="ignore")


def make_chunks(text, size=1000, overlap=150):
    step = size - overlap
    chunks = [text[i : i + size] for i in range(0, len(text), step)]
    return [c for c in chunks if c.strip()]


@st.cache_resource(show_spinner="Loading embedding model...")
def load_embedder():
    return SentenceTransformer("all-MiniLM-L6-v2")


@st.cache_data(show_spinner=False)
def embed(texts):
    return load_embedder().encode(list(texts), normalize_embeddings=True)


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
        "✍️ Text Rewriter",
    ],
)

# =========================================================
# TOOLS
# =========================================================
if tool == "🏠 Home":
    section("✨ Everything You Need for Online Work")
    st.write(
        "AI WorkMate combines multiple AI tools into one simple and professional workspace."
    )

    features = [
        ("🤖", "AI Work Assistant", "Get AI help with your daily online work."),
        ("💼", "Proposal Generator", "Create professional freelancing proposals."),
        ("📧", "Email Generator", "Write professional emails quickly."),
        ("📄", "Resume Analyzer", "Analyze your resume against a job."),
        ("🔎", "Job Analyzer", "Extract skills and requirements from jobs."),
        ("📚", "Document Assistant", "Ask questions from your documents using RAG."),
    ]
    cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(features):
        cols[i % 3].markdown(
            f"""
            <div class="feature-card">
                <div class="feature-icon">{icon}</div>
                <div class="feature-title">{title}</div>
                <div class="feature-description">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.info("💡 Select any AI tool from the sidebar to get started.")

elif tool == "🤖 AI Work Assistant":
    section("🤖 AI Work Assistant")
    task = st.text_area(
        "What do you need help with?",
        height=180,
        placeholder="Example: Help me write a professional message to a client.",
    )
    if st.button("✨ Generate Answer"):
        if task.strip():
            run(clip(task))
        else:
            st.warning("Please enter your task.")

elif tool == "💼 Proposal Generator":
    section("💼 Freelancing Proposal Generator")
    job = st.text_area(
        "📌 Job Description",
        height=220,
        placeholder="Paste the client's job description...",
    )
    skills = st.text_input("🛠️ Your Skills", placeholder="Python, AI, Streamlit, RAG")
    experience = st.text_area("📚 Your Experience")
    tone = st.selectbox("🎨 Proposal Tone", ["Professional", "Friendly", "Short & Direct"])
    if st.button("🚀 Generate Proposal"):
        if job.strip():
            run(
                f"""Create a professional freelancing proposal.

Job:
{clip(job)}

Skills: {skills}
Experience: {experience}
Tone: {tone}

Rules:
- Focus on the client's needs.
- Keep it natural.
- Do not make false claims."""
            )
        else:
            st.warning("Please enter the job description.")

elif tool == "📧 Email Generator":
    section("📧 AI Email Generator")
    recipient = st.text_input("👤 Recipient")
    purpose = st.text_area(
        "📝 Email Purpose",
        height=180,
        placeholder="Example: Follow up with a client who has not replied.",
    )
    tone = st.selectbox("🎨 Email Tone", ["Professional", "Friendly", "Formal", "Short"])
    if st.button("✉️ Generate Email"):
        if purpose.strip():
            run(
                f"""Write a professional email.

Recipient: {recipient}
Purpose: {purpose}
Tone: {tone}

Include: subject, greeting, main message, closing.
Do not invent information."""
            )
        else:
            st.warning("Please enter the email purpose.")

elif tool == "📄 Resume Analyzer":
    section("📄 AI Resume Analyzer")
    resume = st.file_uploader("📤 Upload Resume", type=["pdf", "docx", "txt"])
    job = st.text_area("📌 Paste Job Description", height=220)
    if st.button("🔍 Analyze Resume"):
        if resume and job.strip():
            resume_text = read_file(resume)
            if not resume_text.strip():
                st.error("No text found in this file (it may be a scanned PDF).")
            else:
                run(
                    f"""Analyze this resume against the job description.

RESUME:
{clip(resume_text)}

JOB DESCRIPTION:
{clip(job)}

Provide:
1. Overall match percentage
2. Matching skills
3. Missing skills
4. ATS keywords
5. Resume problems
6. Improvement suggestions
7. Recommended changes

Do not invent information."""
                )
        else:
            st.warning("Upload a resume and enter a job description.")

elif tool == "🔎 Job Description Analyzer":
    section("🔎 Job Description Analyzer")
    job = st.text_area("📌 Paste Job Description", height=300)
    if st.button("🔍 Analyze Job"):
        if job.strip():
            run(
                f"""Analyze this job description:

{clip(job)}

Extract:
1. Job title
2. Required skills
3. Preferred skills
4. Experience requirements
5. Education requirements
6. Technologies
7. ATS keywords
8. Main responsibilities
9. Important requirements"""
            )
        else:
            st.warning("Please enter a job description.")

elif tool == "📚 Document Assistant":
    section("📚 AI Document Assistant")
    uploaded = st.file_uploader("📤 Upload Document", type=["pdf", "docx", "txt"])

    if uploaded:
        text = read_file(uploaded)
        chunks = make_chunks(text)

        if not chunks:
            st.error("No text found in this file (it may be a scanned PDF).")
        else:
            st.success(f"✅ Loaded: {uploaded.name}")
            c1, c2 = st.columns(2)
            c1.metric("Characters Extracted", len(text))
            c2.metric("Document Chunks", len(chunks))

            question = st.text_input("💬 Ask a question about your document")
            if st.button("🔎 Search Document"):
                if question.strip():
                    with st.spinner("Searching document..."):
                        vectors = embed(tuple(chunks))
                        q_vec = embed((question,))[0]
                        scores = vectors @ q_vec  # cosine similarity (normalized)
                        top = np.argsort(scores)[::-1][:3]
                        context = "\n\n".join(chunks[i] for i in top)

                    run(
                        f"""Answer the question using ONLY the document context.

DOCUMENT:
{context}

QUESTION:
{question}

If the answer is not present, say that it was not found in the document."""
                    )
                else:
                    st.warning("Please enter a question.")

elif tool == "📝 AI Summarizer":
    section("📝 AI Summarizer")
    text = st.text_area("Enter text", height=300)
    length = st.selectbox("Summary Length", ["Short", "Medium", "Detailed"])
    if st.button("✨ Create Summary"):
        if text.strip():
            run(
                f"Summarize the following text.\nLength: {length}\n\n"
                f"Text:\n{clip(text)}\n\nKeep the important information."
            )
        else:
            st.warning("Please enter some text.")

elif tool == "✍️ Text Rewriter":
    section("✍️ AI Text Rewriter")
    text = st.text_area("Enter your text", height=250)
    style = st.selectbox(
        "🎨 Rewrite Style", ["Professional", "Simple", "Friendly", "Formal", "Concise"]
    )
    if st.button("✨ Rewrite Text"):
        if text.strip():
            run(
                f"Rewrite this text.\nStyle: {style}\n\nOriginal text:\n{clip(text)}\n\n"
                "Keep the original meaning. Do not add false information."
            )
        else:
            st.warning("Please enter some text.")

# =========================================================
# FOOTER
# =========================================================
st.markdown(
    """
<div class="footer">
    🤖 <b>AI WorkMate</b> — Work Smarter with AI
    <br>
    Built with Python, Streamlit, RAG & AI
</div>
""",
    unsafe_allow_html=True,
)
