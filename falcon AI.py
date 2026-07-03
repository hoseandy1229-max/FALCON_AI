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
    [data-testid="stChatMessage"] { border: 1px solid #39FF14 !important; }
    </style>
""", unsafe_allow_html=True)

# کلاینت‌ها
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"])

# مدیریت وضعیت
if "auth" not in st.session_state: st.session_state.auth = False
if "selected_model" not in st.session_state: st.session_state.selected_model = "mistralai/pixtral-12b:free"

# --- سایدبار ---
with st.sidebar:
    if st.button("Reset"):
        st.session_state.messages = []
        st.rerun()
    
    st.write("بخش:")
    # جابه‌جایی بین مدل‌ها (بدون رمز - در پنل بازشو)
    st.session_state.selected_model = st.selectbox(
        "جابه‌جایی مدل‌ها:",
        ["mistralai/pixtral-12b:free", "google/gemini-2.0-flash-lite-preview-02-05:free", "meta-llama/llama-3.2-11b-vision-instruct"]
    )
    
    # انتخاب بخش
    bot_mode = st.radio("", ["FALCON AI", "SR BOT"])
    
    # ورود به SR BOT با رمز
    if bot_mode == "SR BOT" and not st.session_state.auth:
        pwd = st.text_input("رمز ورود به SR BOT:", type="password")
        if st.button("تایید رمز"):
            if pwd == "1234": st.session_state.auth = True; st.rerun()
            else: st.error("رمز اشتباهه")
    elif bot_mode == "SR BOT" and st.session_state.auth:
        st.success("وارد شدی")
        if st.button("خروج از SR BOT"): st.session_state.auth = False; st.rerun()

st.title("𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰")

# بقیه کدهای نمایش چت و تحلیل عکس...
