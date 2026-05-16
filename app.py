import streamlit as st
import pdfplumber
from groq import Groq
import re
import pandas as pd
import random


client = Groq(api_key="YOUR_API_KEY")


st.set_page_config(page_title="ATS Resume System", layout="wide")

colors = [
    "#1f77ff", "#ff7f50", "#2ecc71", "#9b59b6",
    "#f39c12", "#e74c3c", "#16a085", "#34495e"
]

st.markdown("""
<style>

/* ===== MAIN TITLE ===== */
.main-title {
    text-align: center;
    font-size: 60px;
    font-weight: 700;
    margin-bottom: 30px;
}

/* ===== SECTION HEADINGS ===== */
.section-header {
    font-size: 40px;
    font-weight: 600;
    margin-top: 30px;
    margin-bottom: 10px;
}

/* ===== SUB HEADINGS ===== */
.sub-header {
    font-size: 30px;
    font-weight: 600;
    margin-top: 20px;
    margin-bottom: 8px;
}

/* ===== TEXT AREA LABEL ===== */
div[data-testid="stTextArea"] label {
    font-size: 18px !important;
    font-weight: 600;
}

/* ===== TEXT AREA INPUT ===== */
div[data-testid="stTextArea"] textarea {
    font-size: 20px !important;
    line-height: 1.6;
}

/* ===== GENERAL TEXT ===== */
html, body, [class*="css"] {
    font-size: 18px;
}

</style>
""", unsafe_allow_html=True)

st.markdown(
    "<div class='main-title'>👤 👤 👤 ATS Resume Analyzer 👤 👤 👤</div>",
    unsafe_allow_html=True
)


if "results" not in st.session_state:
    st.session_state.results = []

if "selected_resume" not in st.session_state:
    st.session_state.selected_resume = None

if "ranked" not in st.session_state:
    st.session_state.ranked = False


def extract_text(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


def analyze_resume(resume, jd):

    prompt = f"""
    You are an ATS (Applicant Tracking System).

    Compare the resume with the job description.

    Give output in this EXACT format:

    Match Percentage: XX%

    Summary:
    (4-5 lines only)

    Key Strengths:
    - point
    - point

    Key Weaknesses:
    - point
    - point

    Missing Keywords:
    - keyword
    - keyword

    Suggestions to Improve:
    - suggestion
    - suggestion

    RULES:
    - Keep response Medium and Clear 
    - Use bullet points
    - Use simple English
    - Match percentage must be STRICT (0-100)
    - Be CONSISTENT

    Job Description:
    {jd}

    Resume:
    {resume}
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content


def extract_score(text):
    match = re.search(r'(\d+)', text)
    return int(match.group(1)) if match else 0


def display_result(result):

    score = extract_score(result)

    st.markdown("<div class='sub-header'>📊 Match Score</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="margin-bottom:8px; font-weight:600;">
    {score}% Match
    </div>

    <div style="
    width: 100%;
    height: 18px;
    background: #eee;
    border-radius: 10px;
    overflow: hidden;
    ">
    <div style="
        width: {score}%;
        height: 100%;
        background: linear-gradient(90deg, #1f77ff, #4da6ff);
        border-radius: 10px;
        transition: width 0.6s ease;
    "></div>
    </div>
    """, unsafe_allow_html=True)
    st.write(f"### {score}% Match")

    sections = result.split("\n\n")

    for section in sections:
        if "Summary" in section:
            st.markdown("<div class='sub-header'>📌 Summary</div>", unsafe_allow_html=True)
            st.write(section.replace("Summary:", "").strip())

        elif "Strengths" in section:
            st.markdown("<div class='sub-header'>✅ Strengths</div>", unsafe_allow_html=True)
            st.write(section)

        elif "Weaknesses" in section:
            st.markdown("<div class='sub-header'>📉 Weaknesses</div>", unsafe_allow_html=True)
            st.write(section)

        elif "Missing Keywords" in section:
            st.markdown("<div class='sub-header'>🧩 Missing Keywords From Job Description</div>", unsafe_allow_html=True)
            st.write(section)

        elif "Suggestions" in section:
            st.markdown("<div class='sub-header'>✨ Suggestions To Improve Resume</div>", unsafe_allow_html=True)
            st.write(section)


st.markdown("<div class='sub-header'>Enter Job Description 📝 </div>", unsafe_allow_html=True)
jd = st.text_area("", height=180)


st.markdown(
    "<div class='section-header'>🔍 Single Resume Analysis</div>",
    unsafe_allow_html=True
)

st.markdown("<div class='sub-header'>📄 Upload Resume</div>", unsafe_allow_html=True)
file = st.file_uploader("", type=["pdf"], key="single")

if st.button("Analyze Resume"):

    if file and jd:

        with st.spinner("Analyzing... ⏳"):
            resume_text = extract_text(file)
            result = analyze_resume(resume_text, jd)

        display_result(result)

    else:
        st.warning("Upload resume + enter JD")


st.markdown(
    "<div class='section-header'>📊 Multiple Resume Ranking</div>",
    unsafe_allow_html=True
)

files = st.file_uploader(
    "Upload Multiple Resumes",
    type=["pdf"],
    accept_multiple_files=True
)

if st.button("Rank Resumes"):

    if files and jd:

        st.session_state.results = []
        st.session_state.selected_resume = None

        for f in files:
            with st.spinner(f"Processing {f.name}..."):

                text = extract_text(f)
                res = analyze_resume(text, jd)
                score = extract_score(res)

                st.session_state.results.append({
                    "name": f.name,
                    "score": score,
                    "analysis": res
                })

        st.session_state.results.sort(key=lambda x: x["score"], reverse=True)
        st.session_state.ranked = True

    else:
        st.warning("Upload resumes + JD")


if st.session_state.ranked and st.session_state.results:

    st.markdown(
        "<div class='section-header'>🏆 Ranking Results</div>",
        unsafe_allow_html=True
    )

    for i, r in enumerate(st.session_state.results):

        bg_color = random.choice(colors)

        st.markdown(f"""
        <div style="
        background: {bg_color};
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 15px;
        color: white;
        font-size: 22px;
        font-weight: 600;
        ">
        {i+1}. {r['name']} - {r['score']}%
        </div>
        """, unsafe_allow_html=True)

    st.success(f"🥇 Top Candidate: {st.session_state.results[0]['name']}")

    data = [
        {
            "Rank": i + 1,
            "Resume Name": r["name"],
            "Score": r["score"],
            "Analysis": r["analysis"]
        }
        for i, r in enumerate(st.session_state.results)
    ]

    df = pd.DataFrame(data)

    st.download_button(
        label="📥 Download CSV Report",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="ATS_Resume_Ranking.csv",
        mime="text/csv"
    )