import streamlit as st
import requests
import time
import json
from collections import defaultdict

API_BASE = "http://localhost:8000"

# --------------------
# Sidebar: Model & Template Selection
# --------------------
st.set_page_config(page_title="Multi-Model LLM Chat UI", layout="wide")
st.sidebar.title("Model & Prompt Template Selection")

# Hardcoded model metadata (can be fetched from /models if available)
MODEL_INFOS = {
    "llama-3.1-8b-instant": {"label": "Llama 3.1 8B (Groq)", "tooltip": "Fast, cost-effective, good for general tasks."},
    "llama-3.3-70b-versatile": {"label": "Llama 3.3 70B (Groq)", "tooltip": "Large, high-quality, slower."},
    "deepseek-r1-distill-llama-70b": {"label": "DeepSeek Llama 70B (Groq)", "tooltip": "Distilled, efficient, large context."},
    "meta-llama/llama-4-maverick-17b-128e-instruct": {"label": "Llama 4 Maverick 17B (Groq)", "tooltip": "Instruction-tuned, creative."},
    "meta-llama/llama-4-scout-17b-16e-instruct": {"label": "Llama 4 Scout 17B (Groq)", "tooltip": "Instruction-tuned, fast."},
    "meta-llama/llama-prompt-guard-2-22m": {"label": "Llama Prompt Guard 22M (Groq)", "tooltip": "Guardrail, safety-focused."},
    "meta-llama/llama-prompt-guard-2-86m": {"label": "Llama Prompt Guard 86M (Groq)", "tooltip": "Guardrail, safety-focused."},
    "mistral-saba-24b": {"label": "Mistral Saba 24B (Groq)", "tooltip": "Mistral, large context, fast."},
    "moonshotai/kimi-k2-instruct": {"label": "Moonshot Kimi K2 (Groq)", "tooltip": "Instruction-tuned, large context."},
    "gemini-2.5-pro": {"label": "Gemini 2.5 Pro (Google)", "tooltip": "Google's top model, high quality."},
    "gemini-2.5-flash": {"label": "Gemini 2.5 Flash (Google)", "tooltip": "Fast, cost-effective, good for chat."},
    "gemini-2.5-flash-lite-preview-06-17": {"label": "Gemini 2.5 Flash-Lite Preview (Google)", "tooltip": "Preview, very fast, lower cost."},
    "gemini-2.0-flash": {"label": "Gemini 2.0 Flash (Google)", "tooltip": "Previous gen, fast."},
    "gemini-2.0-flash-lite": {"label": "Gemini 2.0 Flash-Lite (Google)", "tooltip": "Previous gen, very fast."},
}
MODEL_LIST = list(MODEL_INFOS.keys())

# Fetch prompt templates
@st.cache_data(show_spinner=False)
def fetch_templates():
    try:
        resp = requests.get(f"{API_BASE}/templates")
        if resp.status_code == 200:
            return resp.json()
        # fallback: try loading from file
        with open("prompt_templates.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

templates = fetch_templates()
TEMPLATE_CATEGORIES = sorted(set(t.get("category", "Other") for t in templates))
TEMPLATES_BY_CATEGORY = defaultdict(list)
for t in templates:
    TEMPLATES_BY_CATEGORY[t.get("category", "Other")].append(t)

# Sidebar: Model selection
def model_label(model):
    info = MODEL_INFOS.get(model, {})
    return info.get("label", model)

selected_model = st.sidebar.selectbox(
    "Select Model",
    MODEL_LIST,
    format_func=model_label,
    help="Choose which LLM to use for your prompt."
)
if selected_model in MODEL_INFOS:
    st.sidebar.caption(MODEL_INFOS[selected_model]["tooltip"])

# Sidebar: Prompt Template selection
template_mode = st.sidebar.radio("Prompt Mode", ["Raw Prompt", "Template"], index=0)
selected_template = None
if template_mode == "Template":
    for cat in TEMPLATE_CATEGORIES:
        with st.sidebar.expander(f"{cat.title()} ({len(TEMPLATES_BY_CATEGORY[cat])})"):
            for t in TEMPLATES_BY_CATEGORY[cat]:
                if st.button(t["title"], key=f"template_{t['id']}"):
                    st.session_state["selected_template_id"] = t["id"]
    selected_template_id = st.session_state.get("selected_template_id")
    selected_template = next((t for t in templates if t["id"] == selected_template_id), None)
    if selected_template:
        st.sidebar.markdown(f"**{selected_template['title']}**")
        st.sidebar.caption(f"Tags: {', '.join(selected_template.get('tags', []))}")
        st.sidebar.write(selected_template["prompt"])

# --------------------
# Main Content Tabs
# --------------------
tabs = st.tabs(["Chat", "Prompt Templates", "Analytics"])

# --------------------
# Chat Tab
# --------------------
with tabs[0]:
    st.header("Chat with LLM")
    chat_history = st.session_state.get("chat_history", [])
    with st.expander("Advanced Settings", expanded=False):
        ignore_cache = st.checkbox("Ignore Cache (force fresh response)", value=False)
    if template_mode == "Raw Prompt":
        user_prompt = st.text_area("Enter your prompt", key="raw_prompt")
        template_id = None
        template_vars = None
    else:
        user_prompt = None
        template_vars = {}
        if selected_template:
            # Find all {{var}} in the template
            import re
            var_names = set(re.findall(r"\{\{(.*?)\}\}", selected_template["prompt"]))
            for var in var_names:
                template_vars[var] = st.text_input(f"{var}", key=f"var_{var}")
            template_id = selected_template["id"]
        else:
            template_id = None
            template_vars = None
    if st.button("Send Prompt", type="primary"):
        with st.spinner("Contacting backend..."):
            payload = {}
            if template_id:
                payload = {"template_id": template_id, "template_vars": template_vars}
            elif user_prompt:
                payload = {"prompt": user_prompt}
            else:
                st.error("Please enter a prompt or select a template.")
                st.stop()
            try:
                resp = requests.post(
                    f"{API_BASE}/chat?model={selected_model}&ignore_cache={'true' if ignore_cache else 'false'}",
                    json=payload,
                    timeout=60
                )
                if resp.status_code == 200:
                    data = resp.json()
                    chat_history.append({
                        "prompt": user_prompt or (selected_template["prompt"] if selected_template else ""),
                        "template_id": template_id,
                        "template_vars": template_vars,
                        "response": data["response_text"],
                        "model_used": data.get("model_used"),
                        "latency_ms": data.get("latency_ms"),
                        "token_count": data.get("token_count"),
                        "from_cache": data.get("from_cache"),
                        "fallback_used": data.get("fallback_used"),
                        "error_message": data.get("error_message"),
                        "prompt_id": data.get("prompt_id")
                    })
                    st.session_state["chat_history"] = chat_history
                else:
                    st.error(f"Backend error: {resp.status_code} {resp.text}")
                    st.stop()
            except Exception as e:
                st.error(f"Request failed: {e}")
                st.stop()
    # Display chat history
    for i, entry in enumerate(reversed(chat_history[-10:])):
        with st.container():
            st.markdown(f"**Prompt:** {entry['prompt']}")
            if entry.get("template_id"):
                st.caption(f"Template: {entry['template_id']}")
            if entry.get("template_vars"):
                st.caption(f"Vars: {entry['template_vars']}")
            st.markdown(f"**Response:**")
            st.code(entry["response"])
            cols = st.columns([1,1,1,1,1,2])
            cols[0].metric("Model", entry.get("model_used", "?"))
            cols[1].metric("Latency (s)", f"{(entry.get('latency_ms') or 0)/1000:.2f}")
            cols[2].metric("Tokens", entry.get("token_count", "?"))
            cols[3].metric("Cache", "✅" if entry.get("from_cache") else "❌")
            cols[4].metric("Fallback", "⚠️" if entry.get("fallback_used") else "✅")
            if entry.get("error_message"):
                cols[5].error(entry["error_message"])
            # Rating system
            with st.expander("Rate this response", expanded=False):
                rating = st.slider("Rating (1-5)", 1, 5, 3, key=f"rate_{i}")
                feedback = st.text_area("Feedback", key=f"fb_{i}")
                if st.button("Submit Rating", key=f"submit_rate_{i}"):
                    try:
                        rate_payload = {
                            "prompt_id": entry.get("prompt_id"),
                            "model": entry.get("model_used"),
                            "rating": rating,
                            "feedback": feedback
                        }
                        rate_resp = requests.post(f"{API_BASE}/rate", json=rate_payload)
                        if rate_resp.status_code == 200:
                            st.success("Rating submitted!")
                        else:
                            st.error(f"Rating failed: {rate_resp.text}")
                    except Exception as e:
                        st.error(f"Rating error: {e}")
    if st.button("Reset Session"):
        st.session_state["chat_history"] = []
        st.experimental_rerun()

# --------------------
# Prompt Templates Tab
# --------------------
with tabs[1]:
    st.header("Prompt Templates")
    for cat in TEMPLATE_CATEGORIES:
        st.subheader(cat.title())
        for t in TEMPLATES_BY_CATEGORY[cat]:
            with st.expander(f"{t['title']} ({t['id']})"):
                st.write(t["prompt"])
                st.caption(f"Tags: {', '.join(t.get('tags', []))}")
                st.caption(f"Category: {t.get('category', 'Other')}")

# --------------------
# Analytics Tab
# --------------------
with tabs[2]:
    st.header("Real-Time Analytics")
    if st.button("Refresh Stats"):
        st.session_state["last_stats_refresh"] = time.time()
    last_stats = st.session_state.get("last_stats", None)
    if (not last_stats) or (time.time() - st.session_state.get("last_stats_refresh", 0) > 30):
        try:
            stats_resp = requests.get(f"{API_BASE}/stats")
            if stats_resp.status_code == 200:
                stats = stats_resp.json()
                st.session_state["last_stats"] = stats
            else:
                st.error(f"Stats error: {stats_resp.text}")
                stats = None
        except Exception as e:
            st.error(f"Stats fetch failed: {e}")
            stats = None
    else:
        stats = last_stats
    if stats:
        st.subheader("Model Usage")
        st.bar_chart(stats["model_usage"])
        st.subheader("Average Latency (s)")
        st.bar_chart(stats["avg_latency"])
        st.subheader("Average Rating")
        st.bar_chart(stats["avg_rating"])
        st.metric("Total Fallbacks", stats["total_fallbacks"])
        st.metric("Total Prompts", stats["total_prompts"])

# --------------------
# Footer
# --------------------
st.markdown("---")
st.caption("Multi-Model LLM Chat UI | Powered by FastAPI backend | Streamlit frontend | All features covered.") 