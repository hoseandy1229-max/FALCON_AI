import streamlit as st
from groq import Groq
from openai import OpenAI
import urllib.parse

st.set_page_config(page_title="Falcon AI", layout="wide")

# استایل‌دهی
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    [data-testid="stChatMessage"] { background-color: #000000 !important; border: 1px solid #39FF14 !important; }
    [data-testid="stChatMessage"] p { color: #39FF14 !important; }
    </style>
""", unsafe_allow_html=True)

# تنظیم کلاینت‌ها
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"])

st.sidebar.title("تنظیمات")
models = {
    "Llama 3.3 70B (Groq)": {"client": "groq", "name": "llama-3.3-70b-versatile"},
    "Mistral Nemo 12B (Free)": {"client": "or", "name": "mistralai/mistral-nemo"},
    "Qwen 2.5 7B (Free)": {"client": "or", "name": "qwen/qwen-2.5-7b-instruct"},
    "Gemma 2 9B (Free)": {"client": "or", "name": "google/gemma-2-9b-it"}
}

selected_model_key = st.sidebar.selectbox("انتخاب مدل:", list(models.keys()))
tool_mode = st.sidebar.checkbox("حالت تولید تصویر")
mode = st.sidebar.radio("بخش:", ["𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰", "𝑺𝑹 𝑩𝑶𝑻"])

def get_response(messages, is_sara=False):
    model_info = models[selected_model_key]
    
    if is_sara:
        sys = {"role": "system", "content": "تو دستیار شخصی سارا هستی. قوانین: اگر پاسخ تایید است با 'چشم بانو' شروع کن. فقط فارسی بنویس. هیچ کاراکتر غیرفارسی استفاده نکن. پاسخ‌ها کوتاه و بدون حاشیه."}
        target_client = groq_client
        target_model = "llama-3.3-70b-versatile"
        temp = 0.2
    else:
        sys = {"role": "system", "content": "تو دستیار حرفه‌ای هستی. پاسخ‌های کوتاه و دقیق بده."}
        target_client = groq_client if model_info["client"] == "groq" else or_client
        target_model = model_info["name"]
        temp = 0.5
    
    try:
        response = target_client.chat.completions.create(model=target_model, messages=[sys] + messages, temperature=temp)
        return response.choices[0].message.content
    except Exception as e:
        return f"خطا در مدل: {str(e)}"

def render_chat(key, is_sara=False):
    if key not in st.session_state: st.session_state[key] = []
    for msg in st.session_state[key]:
        with st.chat_message(msg["role"]):
            if msg.get("type") == "image": st.markdown(f'<img src="{msg["content"]}" style="width:100%;">', unsafe_allow_html=True)
            else: st.markdown(msg["content"])
            
    if prompt := st.chat_input("Ask..."):
        st.session_state[key].append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            if tool_mode and not is_sara:
                img_url = f"https://pollinations.ai/p/{urllib.parse.quote(prompt)}"
                st.markdown(f'<img src="{img_url}" style="width:100%;">', unsafe_allow_html=True)
                st.session_state[key].append({"role": "assistant", "content": img_url, "type": "image"})
            else:
                resp = get_response(st.session_state[key], is_sara)
                st.markdown(resp)
                st.session_state[key].append({"role": "assistant", "content": resp})
            st.rerun()

if mode == "𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰":
    st.title("𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰")
    render_chat("messages")
else:
    if 'auth' not in st.session_state: st.session_state['auth'] = False
    if not st.session_state['auth']:
        pwd = st.text_input("رمز:", type="password")
        if st.button("تایید ورود"):
            if pwd == "sara": st.session_state['auth'] = True; st.rerun()
            else: st.error("رمز اشتباه است.")
    else:
        render_chat("sara_messages", is_sara=True)
        if st.button("خروج"): st.session_state['auth'] = False; st.rerun()
