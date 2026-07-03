import streamlit as st
from groq import Groq
from openai import OpenAI
import urllib.parse
import random 
import base64

# تنظیمات صفحه
st.set_page_config(page_title="Falcon AI", layout="wide")

# استایل سبز نئونی (کادر و حباب پیام‌ها)
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

if "auth" not in st.session_state: st.session_state.auth = False

# --- سایدبار ---
with st.sidebar:
    if st.button("Reset"):
        st.session_state.messages = []
        st.rerun()
    
    st.write("بخش:")
    bot_mode = st.radio("", ["FALCON AI", "SR BOT"])
    
    st.write("---")
    model_choice = st.selectbox("انتخاب مدل:", [
        "mistralai/pixtral-12b:free", 
        "google/gemini-2.0-flash-lite-preview-02-05:free",
        "meta-llama/llama-3.2-11b-vision-instruct"
    ])

# منطق ورود به SR BOT
if bot_mode == "SR BOT" and not st.session_state.auth:
    pwd = st.text_input("رمز SR BOT:", type="password")
    if st.button("ورود"):
        if pwd == "1234": 
            st.session_state.auth = True
            st.session_state.messages = [{"role": "assistant", "content": "سلام سارا جون."}]
            st.rerun()
        else: st.error("رمز اشتباه است!")
    st.stop() # برنامه در اینجا متوقف می‌شود تا رمز وارد شود

st.title("𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰")

mode = st.radio("حالتِ کاری:", ["💬 چت عادی", "🎨 تولید تصویر", "👁️ تحلیل عکس"], horizontal=True)

if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image_gen": st.image(msg["content"])
        else: st.markdown(msg["content"])

# --- پردازش پاسخ‌ها ---
def get_ai_response(prompt_text):
    # اگر در حالت SR BOT است، لحنِ مطیع و اضافه کردنِ "چشم بانو" فقط در پاسخ‌های کاری
    system_msg = "You are a helpful assistant."
    if bot_mode == "SR BOT":
        system_msg = "تو یک دستیارِ مطیع هستی. اگر کاربر دستور کاری داد، پاسخ بده و در انتها حتما بگو: چشم بانو. اگر سوال معمولی بود، عادی پاسخ بده."
    
    res = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": prompt_text}]
    ).choices[0].message.content
    return res

# --- بخش چت ---
if prompt := st.chat_input("پیام خود را بنویسید..."):
    if mode != "👁️ تحلیل عکس":
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        if mode == "💬 چت عادی":
            res = get_ai_response(prompt)
            st.markdown(res)
            st.session_state.messages.append({"role": "assistant", "content": res})
        elif mode == "🎨 تولید تصویر":
            url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&seed={random.randint(1,999999)}"
            st.image(url)
            st.session_state.messages.append({"role": "assistant", "content": url, "type": "image_gen"})
    if mode != "👁️ تحلیل عکس": st.rerun()
