import streamlit as st
from groq import Groq
import urllib.parse

st.set_page_config(page_title="Falcon AI", layout="wide")

# استایل‌دهی (مشکی و سبز فسفوری)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    [data-testid="stChatMessage"] { background-color: #000000 !important; border: 1px solid #39FF14 !important; }
    [data-testid="stChatMessage"] p { color: #39FF14 !important; }
    </style>
""", unsafe_allow_html=True)

api_key = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=api_key)

# تنظیمات مدل و ابزار در سایدبار
st.sidebar.title("پنل تنظیمات")
model_choice = st.sidebar.selectbox("انتخاب مدل:", ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"])
tool_mode = st.sidebar.checkbox("حالت تولید تصویر")

if st.sidebar.button("Reset"): st.session_state.clear(); st.rerun()

# توابع پاسخ
def get_response(messages, is_sara=False):
    if is_sara:
        sys = {"role": "system", "content": "تو دستیار شخصی سارا هستی. فقط و فقط با عبارت 'چشم بانو' پاسخ را شروع کن. مطلقاً حرف اضافه نزن. هذیان نگو."}
    else:
        sys = {"role": "system", "content": "دستیار دقیق و حرفه‌ای."}
    
    response = client.chat.completions.create(model=model_choice, messages=[sys] + messages)
    return response.choices[0].message.content

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

# بدنه اصلی
mode = st.sidebar.radio("بخش:", ["𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰", "𝑺𝑹 𝑩𝑶𝑻"])
if mode == "𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰":
    st.title("𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰")
    render_chat("messages")
else:
    if 'auth' not in st.session_state: st.session_state['auth'] = False
    if not st.session_state['auth']:
        if st.text_input("رمز:", type="password") == "sara" and st.button("تایید"):
            st.session_state['auth'] = True; st.rerun()
    else:
        render_chat("sara_messages", is_sara=True)
        if st.button("خروج"): st.session_state['auth'] = False; st.rerun()
