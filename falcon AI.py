import streamlit as st
from groq import Groq
import random

st.set_page_config(page_title="Falcon AI", layout="wide")

# استایل سبز نئونی
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    [data-testid="stChatMessage"] { 
        border: 2px solid #39FF14 !important; 
        background-color: #1a1d23 !important;
        border-radius: 15px !important;
        padding: 10px !important;
    }
    </style>
""", unsafe_allow_html=True)

groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "auth_sr" not in st.session_state: st.session_state.auth_sr = False
if "messages_falcon" not in st.session_state: st.session_state.messages_falcon = []
if "messages_sr" not in st.session_state: st.session_state.messages_sr = []

# --- سایدبار ---
with st.sidebar:
    bot_mode = st.radio("بخش:", ["FALCON AI", "SR BOT"])
    
    # جابه‌جایی مدل‌ها (همیشه باز و بدون رمز)
    selected_model = st.selectbox("مدل:", [
        "llama-3.3-70b-versatile", 
        "mixtral-8x7b-32768", 
        "gemma2-9b-it"
    ])
    
    if st.button("Reset"):
        if bot_mode == "SR BOT": st.session_state.messages_sr = []
        else: st.session_state.messages_falcon = []
        st.rerun()

# مدیریت ورود به SR BOT
if bot_mode == "SR BOT" and not st.session_state.auth_sr:
    pwd = st.text_input("رمز ورود به SR BOT:", type="password")
    if st.button("تایید"):
        if pwd == "1234":
            st.session_state.auth_sr = True
            st.session_state.messages_sr = [{"role": "assistant", "content": "سلام سارا جون."}]
            st.rerun()
        else: st.error("رمز اشتباهه!")
    st.stop()

# انتخاب محتوا
current_messages = st.session_state.messages_sr if bot_mode == "SR BOT" else st.session_state.messages_falcon
st.title("مخصوص سارا" if bot_mode == "SR BOT" else "𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰")

for msg in current_messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# پردازش چت
if prompt := st.chat_input("پیام خود را بنویسید..."):
    current_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        sys_prompt = "تو دستیار سارا هستی. اگر دستور کاری بود آخرش بگو: چشم بانو." if bot_mode == "SR BOT" else "کوتاه پاسخ بده."
        
        res = groq_client.chat.completions.create(
            model=selected_model,
            messages=[{"role": "system", "content": sys_prompt}] + current_messages
        ).choices[0].message.content
        
        st.markdown(res)
        current_messages.append({"role": "assistant", "content": res})
