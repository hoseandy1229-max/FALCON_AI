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

# تعریف کلاینت‌ها
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"])

if "auth_sr" not in st.session_state: st.session_state.auth_sr = False
if "messages_falcon" not in st.session_state: st.messages_falcon = []
if "messages_sr" not in st.session_state: st.messages_sr = []

# --- سایدبار ---
with st.sidebar:
    bot_mode = st.radio("بخش:", ["FALCON AI", "SR BOT"])
    # مدل انتخاب شده در اینجا ذخیره می‌شود
    selected_model = st.selectbox("انتخاب مدل:", [
        "llama-3.3-70b-versatile",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ])
    if st.button("Reset"):
        if bot_mode == "SR BOT": st.session_state.messages_sr = []
        else: st.session_state.messages_falcon = []
        st.rerun()

# لاگین
if bot_mode == "SR BOT" and not st.session_state.auth_sr:
    if st.text_input("رمز:", type="password") == "1234":
        st.session_state.auth_sr = True
        st.session_state.messages_sr = [{"role": "assistant", "content": "سلام سارا جون."}]
        st.rerun()
    st.stop()

current_messages = st.session_state.messages_sr if bot_mode == "SR BOT" else st.session_state.messages_falcon
st.title("مخصوص سارا" if bot_mode == "SR BOT" else "𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰")

mode = st.radio("حالت:", ["💬 چت عادی", "🎨 تولید تصویر", "👁️ تحلیل عکس"], horizontal=True)

for msg in current_messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image_gen": st.image(msg["content"])
        else: st.markdown(msg["content"])

# --- پردازش ---
if prompt := st.chat_input("پیام..."):
    current_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        if mode == "🎨 تولید تصویر":
            translation = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role":"system", "content":"Translate to detailed English prompt."}, {"role":"user", "content":prompt}]
            ).choices[0].message.content
            url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(translation)}?width=1024&height=1024&seed={random.randint(1,99999)}"
            st.image(url)
            current_messages.append({"role": "assistant", "content": url, "type": "image_gen"})
        else:
            # مدل استفاده شده در اینجا همان selected_model است که در سایدبار انتخاب کردی
            sys = f"You are using model {selected_model}. تو دستیار سارایی. برای دستور کاری بگو چشم بانو." if bot_mode=="SR BOT" else f"You are {selected_model}. کوتاه پاسخ بده."
            res = groq_client.chat.completions.create(
                model=selected_model, 
                messages=[{"role":"system", "content":sys}]+current_messages
            ).choices[0].message.content
            st.markdown(res)
            current_messages.append({"role": "assistant", "content": res})
    st.rerun()
