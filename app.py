from importlib.resources import files

import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DocIQ — RAG Document Intelligence",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.stApp {
            background: #FFFFFF !important;
}

.main {
            background: #FFFFFF !important;
            color: #111827 !important;
}
            
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

body, input, button, select, textarea, p, span, div, h1, h2, h3, h4, h5, h6, a { font-family: 'Inter', sans-serif !important; }

/* ── Layout ── */
.main .block-container {
    padding: 2.25rem 3rem;
    max-width: 960px;
    background: #FFFFFF;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #FAFAFA;
    border-right: 1px solid #E5E7EB;
}
[data-testid="stSidebar"] * { color: #374151 !important; }

[data-testid="stSidebar"] .stButton > button {
    background: #FFFFFF;
    color: #374151 !important;
    border: 1px solid #D1D5DB;
    border-radius: 6px;
    width: 100%;
    padding: 0.45rem 0.75rem;
    font-weight: 500;
    font-size: 0.8125rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    transition: background 0.15s, border-color 0.15s;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #F9FAFB;
    border-color: #9CA3AF;
}

/* ── File uploader ── */
[data-testid="stSidebar"] [data-testid="stFileUploader"] {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
}

/* ── Main area buttons ── */
.stButton > button {
    border-radius: 6px;
    font-weight: 500;
    font-size: 0.875rem;
    padding: 0.45rem 1rem;
    transition: all 0.15s;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 1px solid #E5E7EB;
    background: transparent;
    margin-bottom: 1.5rem;
}
.stTabs [data-baseweb="tab"] {
    padding: 0.625rem 1.25rem;
    font-weight: 500;
    font-size: 0.875rem;
    color: #6B7280;
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
    border-radius: 0;
}
.stTabs [aria-selected="true"] {
    color: #111827 !important;
    background: transparent !important;
    border-bottom: 2px solid #2563EB !important;
    font-weight: 600;
}

/* ── Answer block ── */
.answer-block {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-left: 3px solid #2563EB;
    border-radius: 0 8px 8px 0;
    padding: 1.25rem 1.5rem;
    font-size: 0.9375rem;
    line-height: 1.8;
    color: #111827;
    margin: 0.5rem 0 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

/* ── Section labels ── */
.section-title {
    font-size: 0.6875rem;
    font-weight: 600;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: #6B7280;
    margin: 1.75rem 0 0.6rem;
}

/* ── Source pills ── */
.source-pill {
    display: inline-block;
    background: #F3F4F6;
    border: 1px solid #E5E7EB;
    color: #374151;
    border-radius: 4px;
    padding: 0.2rem 0.65rem;
    font-size: 0.8rem;
    font-weight: 500;
    margin-right: 0.4rem;
    margin-bottom: 0.4rem;
}

/* ── Badges ── */
.badge {
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 4px;
    font-weight: 600;
    font-size: 0.75rem;
    letter-spacing: 0.02em;
}
.badge-positive { background: #ECFDF5; color: #065F46; }
.badge-negative { background: #FEF2F2; color: #991B1B; }
.badge-neutral  { background: #F3F4F6; color: #374151; }

/* ── Insight / action rows ── */
.insight-row {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.75rem 0;
    border-bottom: 1px solid #F3F4F6;
}
.action-row {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.75rem 0;
    border-bottom: 1px solid #F3F4F6;
}

/* ── Chunk cards ── */
.chunk-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 1.125rem 1.25rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

/* ── Empty states ── */
.empty-state {
    text-align: center;
    padding: 6rem 2rem;
    color: #9CA3AF;
}

/* ── Status messages ── */
.status-ok {
    background: #F0FDF4;
    border: 1px solid #BBF7D0;
    border-radius: 6px;
    padding: 0.625rem 0.875rem;
    color: #166534;
    font-size: 0.8125rem;
    margin-top: 0.75rem;
}
.status-err {
    background: #FEF2F2;
    border: 1px solid #FECACA;
    border-radius: 6px;
    padding: 0.625rem 0.875rem;
    color: #991B1B;
    font-size: 0.8125rem;
    margin-top: 0.75rem;
}

/* ── Misc ── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for key in ["analysis_result", "query_result", "index_status", "selected_history_id"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ── Helpers ───────────────────────────────────────────────────────────────────
def api_get(path, timeout=5):
    """GET request; returns (ok, data_or_message)."""
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=timeout)
        return r.status_code == 200, r.json()
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to the API. Is the server running?"
    except Exception as e:
        return False, str(e)

def api_post_file(path, file_obj, params=None, timeout=60):
    """POST multipart file upload; returns (ok, data_or_message)."""
    try:
        r = requests.post(
            f"{API_BASE}{path}",
            files={"file": (file_obj.name, file_obj.getvalue(), file_obj.type or "text/plain")},
            params=params,
            timeout=timeout
        )
        if r.status_code == 200:
            return True, r.json()
        return False, r.json().get("detail", f"Error {r.status_code}")
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to the API. Is the server running?"
    except Exception as e:
        return False, str(e)

def api_post_query(question, timeout=30):
    """POST /query with question as query param; returns (ok, data_or_message)."""
    try:
        r = requests.post(
            f"{API_BASE}/query",
            params={"question": question},
            timeout=timeout
        )
        if r.status_code == 200:
            return True, r.json()
        return False, r.json().get("detail", f"Error {r.status_code}")
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to the API. Is the server running?"
    except Exception as e:
        return False, str(e)

def sentiment_badge(sentiment):
    s = (sentiment or "").strip().lower()
    css = "badge-positive" if s == "positive" else "badge-negative" if s == "negative" else "badge-neutral"
    label = sentiment or "Neutral"
    return f'<span class="badge {css}">{label}</span>'

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Branding
    st.markdown("""
    <div style="padding:1rem 0 0.5rem;">
        <div style="font-size:1.25rem;font-weight:700;color:#111827;letter-spacing:-0.02em;">DocIQ</div>
        <div style="font-size:0.75rem;color:#9CA3AF;margin-top:0.2rem;font-weight:400;letter-spacing:0.01em;">RAG Document Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    # API status
    api_ok, api_data = api_get("/")
    if api_ok:
        version = api_data.get("version", "")
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:6px;margin:0.5rem 0 1.25rem;">'
            f'<div style="width:6px;height:6px;border-radius:50%;background:#10B981;flex-shrink:0;"></div>'
            f'<span style="font-size:0.75rem;color:#6B7280;">API v{version} connected</span></div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:6px;margin:0.5rem 0 1.25rem;">'
            '<div style="width:6px;height:6px;border-radius:50%;background:#EF4444;flex-shrink:0;"></div>'
            '<span style="font-size:0.75rem;color:#EF4444;font-weight:500;">API offline</span></div>',
            unsafe_allow_html=True
        )

    st.markdown('<div style="height:1px;background:#E5E7EB;margin-bottom:1.25rem;"></div>', unsafe_allow_html=True)

    # File uploader
    st.markdown('<div style="font-size:0.6875rem;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:#9CA3AF;margin-bottom:0.5rem;">Document</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload",
        type=None,
        label_visibility="collapsed"
    )

    if uploaded_file:
        size_kb = len(uploaded_file.getvalue()) / 1024
        st.markdown(
            f'<div style="font-size:0.8rem;color:#6B7280;margin:0.3rem 0 0.9rem;">'
            f'📄 {uploaded_file.name} &nbsp;·&nbsp; {size_kb:.1f} KB</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)

    # Action buttons
    col_a, col_b = st.columns(2)
    with col_a:
        index_clicked = st.button("Index for RAG", use_container_width=True)
    with col_b:
        analyze_clicked = st.button("AI Analysis", use_container_width=True)

    # ── Index action ──
    if index_clicked:
        if not uploaded_file:
            st.warning("Upload a file first.")
        elif not api_ok:
            st.error("API is offline.")
        else:
            with st.spinner("Indexing document…"):
                ok, data = api_post_file("/index", uploaded_file)
                st.session_state.index_status = {"ok": ok, "data": data}

    if st.session_state.index_status:
        s = st.session_state.index_status
        if s["ok"]:
            d = s["data"]
            st.markdown(
                f'<div class="status-ok">'
                f'✓ <strong>{d["filename"]}</strong> ready<br>'
                f'<span style="font-size:0.75rem;">{d["chunks_indexed"]} chunks indexed</span>'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(f'<div class="status-err">⚠ {s["data"]}</div>', unsafe_allow_html=True)

    # ── Analyze action ──
    if analyze_clicked:
        if not uploaded_file:
            st.warning("Upload a file first.")
        elif not api_ok:
            st.error("API is offline.")
        else:
            with st.spinner("Running AI analysis… this may take a moment."):
                ok, data = api_post_file("/analyze-ai", uploaded_file, timeout=120)
                st.session_state.analysis_result = {"ok": ok, "data": data}

    # ── History ──
    st.markdown('<div style="height:1px;background:#E5E7EB;margin:1.5rem 0 1rem;"></div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.6875rem;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:#9CA3AF;margin-bottom:0.75rem;">Recent Analyses</div>', unsafe_allow_html=True)

    if api_ok:
        hist_ok, hist_data = api_get("/history")
        if hist_ok:
            analyses = hist_data.get("analyses", [])
            if analyses:
                for item in analyses[:6]:
                    preview = (item.get("original_text") or "")[:45].strip()
                    wc = item.get("word_count", "—")
                    rl = item.get("reading_level", "")
                    label = f"{preview}…\n{wc} words · {rl}"
                    is_active = st.session_state.selected_history_id == item["id"]
                    if st.button(label, key=f"hist_{item['id']}", use_container_width=True,
                                 type="primary" if is_active else "secondary"):
                        ok, data = api_get(f"/history/{item['id']}")
                        if ok:
                            st.session_state.analysis_result = {"ok": True, "data": data}
                            st.session_state.selected_history_id = item["id"]
                        else:
                            st.error("Could not load analysis details.")
                        
            else:
                st.markdown('<div style="font-size:0.8rem;color:#9CA3AF;">No analyses yet.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="font-size:0.8rem;color:#9CA3AF;">Could not load history.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:0.8rem;color:#9CA3AF;">Connect API to load history.</div>', unsafe_allow_html=True)


# ── Main area ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:2rem;">
    <h1 style="font-size:1.625rem;font-weight:700;color:#111827;letter-spacing:-0.025em;margin:0 0 0.375rem;">
        Document Intelligence
    </h1>
    <p style="color:#6B7280;font-size:0.9rem;margin:0;line-height:1.6;font-weight:400;">
        Index documents for RAG-powered Q&amp;A, or run a full AI analysis — summaries, sentiment, insights, and action items.
    </p>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Ask Questions", "Document Analysis"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — Ask Questions
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    if not api_ok:
        st.error("The API is not running. Start the FastAPI server (`uvicorn main:app --reload`) and refresh.")
    else:
        # Question input row
        q_col, btn_col = st.columns([6, 1])
        with q_col:
            question = st.text_input(
                "question",
                placeholder="e.g. What are the main findings of the report?",
                label_visibility="collapsed"
            )
        with btn_col:
            ask_clicked = st.button("Ask →", use_container_width=True, type="primary")

        if ask_clicked:
            if not question.strip():
                st.warning("Enter a question first.")
            else:
                with st.spinner("Searching your documents…"):
                    ok, data = api_post_query(question)
                    st.session_state.query_result = {"ok": ok, "data": data}

        # Results
        if st.session_state.query_result:
            r = st.session_state.query_result

            if not r["ok"]:
                st.markdown(f'<div class="status-err">⚠ {r["data"]}</div>', unsafe_allow_html=True)
            else:
                d = r["data"]

                # Answer
                st.markdown('<div class="section-title">Answer</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="answer-block">{d["answer"]}</div>', unsafe_allow_html=True)

                # Sources
                if d.get("sources"):
                    st.markdown('<div class="section-title">Sources</div>', unsafe_allow_html=True)
                    pills = "".join(f'<span class="source-pill">📄 {s}</span>' for s in d["sources"])
                    st.markdown(f'<div style="margin-bottom:1.25rem;">{pills}</div>', unsafe_allow_html=True)

                # Matched passages
                if d.get("chunks_used"):
                    st.markdown('<div class="section-title">Matched Passages</div>', unsafe_allow_html=True)
                    for chunk in d["chunks_used"]:
                        score = float(chunk["similarity_score"])
                        score_pct = f"{score:.0%}"
                        score_color = "#059669" if score >= 0.7 else "#D97706" if score >= 0.5 else "#9CA3AF"

                        with st.container():
                            st.markdown(
                                f'<div class="chunk-card">'
                                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.625rem;">'
                                f'<span style="font-size:0.8rem;color:#374151;font-weight:600;">📄 {chunk["document"]}</span>'
                                f'<span style="font-size:0.75rem;font-weight:600;color:{score_color};">{score_pct} match</span>'
                                f'</div>'
                                f'<div style="font-size:0.875rem;color:#6B7280;line-height:1.7;font-style:italic;">"{chunk["excerpt"]}"</div>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                            st.progress(score)

                st.markdown(
                    f'<div style="font-size:0.7rem;color:#9CA3AF;text-align:right;margin-top:0.75rem;">'
                    f'Answered {d.get("answered_at", "")}</div>',
                    unsafe_allow_html=True
                )
        else:
            st.markdown("""
            <div class="empty-state">
                <div style="font-size:2rem;margin-bottom:1rem;">💬</div>
                <div style="font-size:0.9375rem;font-weight:600;color:#374151;margin-bottom:0.4rem;">No question asked yet</div>
                <div style="font-size:0.875rem;color:#9CA3AF;line-height:1.7;">
                    Use <strong style="color:#374151;">Index for RAG</strong> in the sidebar to index a document,<br>then type a question above.
                </div>
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — Document Analysis
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    if not api_ok:
        st.error("The API is not running. Start the FastAPI server and refresh.")
    elif st.session_state.analysis_result is None:
        st.markdown("""
        <div class="empty-state">
            <div style="font-size:2rem;margin-bottom:1rem;">📊</div>
            <div style="font-size:0.9375rem;font-weight:600;color:#374151;margin-bottom:0.4rem;">No analysis yet</div>
            <div style="font-size:0.875rem;color:#9CA3AF;line-height:1.7;">
                Upload a document and click <strong style="color:#374151;">AI Analysis</strong> in the sidebar.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        r = st.session_state.analysis_result

        if not r["ok"]:
            st.markdown(f'<div class="status-err">⚠ {r["data"]}</div>', unsafe_allow_html=True)
        else:
            d = r["data"]
            ai = d.get("ai_analysis") or {}

            # Document title + sentiment badge
            col_name, col_badge = st.columns([4, 1])
            with col_name:
                st.markdown(
                    f'<div style="font-size:1rem;font-weight:600;color:#111827;padding-top:4px;">'
                    f'📄 {d.get("filename", "Document")}</div>',
                    unsafe_allow_html=True
                )
            with col_badge:
                st.markdown(
                    f'<div style="text-align:right;padding-top:6px;">{sentiment_badge(ai.get("sentiment"))}</div>',
                    unsafe_allow_html=True
                )

            st.markdown('<div style="height:1px;background:#E5E7EB;margin:0.875rem 0 1.125rem;"></div>', unsafe_allow_html=True)

            # Stats row
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Word Count", f'{d.get("word_count", 0):,}')
            with m2:
                st.metric("Reading Level", d.get("reading_level", "—"))
            with m3:
                st.metric("Sentiment", ai.get("sentiment", "—"))

            # Summary
            st.markdown('<div class="section-title">Summary</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="answer-block">{ai.get("summary", "No summary available.")}</div>',
                unsafe_allow_html=True
            )

            # Key insights
            insights = ai.get("key_insights") or []
            if insights:
                st.markdown('<div class="section-title">Key Insights</div>', unsafe_allow_html=True)
                for insight in insights:
                    st.markdown(
                        f'<div class="insight-row">'
                        f'<span style="color:#2563EB;font-weight:600;font-size:0.875rem;flex-shrink:0;margin-top:2px;">→</span>'
                        f'<span style="color:#374151;font-size:0.9rem;line-height:1.7;">{insight}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

            # Action items
            actions = ai.get("action_items") or []
            if actions:
                st.markdown('<div class="section-title">Action Items</div>', unsafe_allow_html=True)
                for i, action in enumerate(actions, 1):
                    st.markdown(
                        f'<div class="action-row">'
                        f'<span style="background:#EFF6FF;color:#2563EB;font-weight:600;font-size:0.7rem;'
                        f'padding:0.15rem 0.5rem;border-radius:4px;flex-shrink:0;margin-top:3px;">{i}</span>'
                        f'<span style="color:#374151;font-size:0.9rem;line-height:1.7;">{action}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.markdown(
                    '<div style="color:#9CA3AF;font-size:0.875rem;padding:0.5rem 0;margin-top:0.25rem;">'
                    'No action items identified.</div>',
                    unsafe_allow_html=True
                )

            st.markdown(
                f'<div style="font-size:0.7rem;color:#9CA3AF;text-align:right;margin-top:1.5rem;">'
                f'Analyzed {d.get("analyzed_at", "")}</div>',
                unsafe_allow_html=True
            )
