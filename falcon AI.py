import streamlit as st
from groq import Groq
from openai import OpenAI
import urllib.parse
import random 
import base64

# تنظیمات صفحه
st.set_page_config(page_title="Falcon AI", layout="wide")

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

# کلاینت‌ها
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"])

# مدیریت وضعیت
if "auth" not in st.session_state: st.session_state.auth = False
if "messages_falcon" not in st.session_state: st.session_state.messages_falcon = []
if "messages_sr" not in st.session_state: st.session_state.messages_sr = []

# --- سایدبار ---
with st.sidebar:
    st.write("بخش:")
    bot_mode = st.radio("", ["FALCON AI", "SR BOT"])
    
    st.write("---")
    model_choice = st.selectbox("انتخاب مدل:", ["mistralai/pixtral-12b:free", "google/gemini-2.0-flash-lite-preview-02-05:free"])

# منطق ورود
if bot_mode == "SR BOT" and not st.session_state.auth:
    pwd = st.text_input("رمز SR BOT:", type="password")
    if st.button("ورود"):
        if pwd == "1234": 
            st.session_state.auth = True
            if not st.session_state.messages_sr:
                st.session_state.messages_sr = [{"role": "assistant", "content": "سلام سارا جون."}]
            st.rerun()
        else: st.error("رمز اشتباه است!")
    st.stop()

# انتخاب محتوا بر اساس مود
current_messages = st.session_state.messages_sr if bot_mode == "SR BOT" else st.session_state.messages_falcon
# تغییر عنوان بر اساس بخش انتخاب شده
page_title = "مخصوص سارا" if bot_mode == "SR BOT" else "𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰"

st.title(page_title)

# نمایش پیام‌های همان بخش
for msg in current_messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image_gen": st.image(msg["content"])
        else: st.markdown(msg["content"])

# --- پردازش پاسخ‌ها ---
def process_chat(prompt):
    system_prompt = "کوتاه و فارسی پاسخ بده."
    if bot_mode == "SR BOT":
        system_prompt = "تو دستیارِ سارا هستی. اگر دستورِ کاری هست، پاسخ بده و آخرش حتما بگو: چشم بانو."
    
    res = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": system_prompt}] + current_messages + [{"role": "user", "content": prompt}]
    ).choices[0].message.content
    return res

# --- ورودی کاربر ---
if prompt := st.chat_input("پیام خود را بنویسید..."):
    current_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        res = process_chat(prompt)
        st.markdown(res)
        current_messages.append({"role": "assistant", "content": res})
    st.rerun()
