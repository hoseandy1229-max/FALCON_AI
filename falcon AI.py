import streamlit as st
from groq import Groq
from openai import OpenAI
import urllib.parse
import random 
import base64
import json
import os
from streamlit_cookies_manager import EncryptedCookieManager
from gtts import gTTS
from io import BytesIO
import PyPDF2

# مدیریت کوکی
cookies = EncryptedCookieManager(prefix="falcon_ai", password="some_secret_password")
if not cookies.ready(): st.stop()

if not os.path.exists("history"): os.makedirs("history")
st.set_page_config(page_title="Falcon AI", layout="wide")

# استایل‌ها
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    h1 { text-align: center !important; }
    [data-testid="stChatMessage"] { border: 2px solid #39FF14 !important; background-color: #1a1d23 !important; border-radius: 15px !important; padding: 10px !important; }
    </style>
""", unsafe_allow_html=True)

# توابع کمکی
def text_to_speech(text):
    try:
        # استفاده از کد زبان 'fa' با اطمینان بیشتر
        tts = gTTS(text=text, lang='fa', slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except:
        return None

def extract_file_text(uploaded_file):
    text = ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages: text += page.extract_text() or ""
        else:
            text = uploaded_file.getvalue().decode("utf-8")
    except: text = "خطا در خواندن فایل"
    return text

# تنظیمات کلاینت‌ها (مانند کد اصلی)
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"])

# [بخش‌های لاگین، متغیرهای سشن و تعریف vision_model_options دقیقاً مانند کد اصلی شما...]
# (به دلیل محدودیت کاراکتر، فرض بر وجود این بخش‌هاست)

# سایدبار + پنل ادمین که می‌خواستید
with st.sidebar:
    st.write(f"کاربر: {st.session_state.get('username', 'مهمان')}")
    # ... (کدهای سایدبار شما)
    
    # بازگرداندن پنل ادمین
    with st.expander("🔐 پنل ادمین"):
        admin_pwd = st.text_input("رمز:", type="password")
        if admin_pwd == "admin123":
            sel_u = st.selectbox("کاربر:", os.listdir("history/"))
            if sel_u:
                sel_f = st.selectbox("چت:", os.listdir(f"history/{sel_u}"))
                if sel_f and st.button("مشاهده"):
                    with open(f"history/{sel_u}/{sel_f}", 'r') as file:
                        for msg in json.load(file): st.write(f"**{msg['role']}:** {msg.get('content', '')}")
        elif admin_pwd: st.error("رمز غلط")

# لیست پیام‌ها و نمایش
current_messages = st.session_state.messages_sr if st.session_state.bot_mode == "SR BOT" else st.session_state.messages_falcon

for i, msg in enumerate(current_messages):
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image_gen": st.image(msg["content"])
        else: st.markdown(msg["content"])
        
        # اصلاح دکمه پخش صدا با چک کردن امنیت
        if msg["role"] == "assistant" and msg.get("type") != "image_gen":
            if st.button("🔊 پخش", key=f"audio_{i}"):
                audio_data = text_to_speech(msg["content"])
                if audio_data: st.audio(audio_data, format="audio/mp3")
                else: st.error("خطا در تولید صدا")

# [بخش input و لاجیک‌های بعدی مانند کد قبلی...]
