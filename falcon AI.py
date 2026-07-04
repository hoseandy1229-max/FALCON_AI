import streamlit as st
from groq import Groq
from openai import OpenAI
import urllib.parse
import random 
import base64
import json
import os
from datetime import datetime
from streamlit_cookies_manager import EncryptedCookieManager

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

# سیستم شخصیت‌ها
PERSONAS = {
    "دانا (دانشمند)": "تو یک دانشمند هستی که با دقت و علمی پاسخ می‌دهی.",
    "سارا (دوست‌داشتنی)": "تو یک دوست صمیمی و مهربان هستی که با لحن گرم صحبت می‌کنی.",
    "استاد (سخت‌گیر)": "تو یک استاد سخت‌گیر هستی که به طور مختصر و فنی پاسخ می‌دهی.",
    "شوخ (طناز)": "تو همیشه با شوخی و طنز پاسخ می‌دهی.",
    "فیلسوف (متفکر)": "تو با دیدگاه فلسفی و عمیق به سوالات نگاه می‌کنی.",
    "نویسنده (خلاق)": "تو با ادبیاتی شاعرانه و خلاقانه پاسخ می‌دهی.",
    "کدنویس (منطقی)": "تو تمرکزت روی منطق و حل مسئله است و پاسخ‌های ساختاریافته می‌دهی.",
    "مربی (انگیزشی)": "تو پاسخ‌هایت پر از انرژی و انگیزه‌بخشی است.",
    "کارآگاه (تحلیل‌گر)": "تو با نگاهی پرسشگر و جزئی‌نگر پاسخ می‌دهی."
}

vision_model_options = {
    "اتوماتیک": "auto", "Gemma 4": "google/gemma-4-31b-it", "Nemotron": "nvidia/nemotron-3-nano-omni",
    "Gemini Flash": "google/gemini-2.5-flash", "Llama 3.2 Vision": "meta-llama/llama-3.2-11b-vision-instruct",
    "Qwen VL": "qwen/qwen-2-vl-72b-instruct", "Pixtral": "mistralai/pixtral-12b"
}

def analyze_image(uploaded_file, user_prompt, model_to_use):
    bytes_data = uploaded_file.getvalue()
    base64_image = base64.b64encode(bytes_data).decode('utf-8')
    target_models = [m for m in vision_model_options.values() if m != "auto"] if model_to_use == "auto" else [model_to_use]
    for model in target_models:
        try:
            response = or_client.chat.completions.create(model=model, messages=[{"role": "user", "content": [
                {"type": "text", "text": user_prompt or "این عکس را تحلیل کن"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}])
            return response.choices[0].message.content
        except: continue
    return "خطا در تحلیل تصویر."

# لاگین
if "username" not in st.session_state:
    if "username" in cookies: st.session_state.username = cookies["username"]
    else:
        st.title("ورود به Falcon AI")
        user_input = st.text_input("نام کاربری:")
        if st.button("تایید"): st.session_state.username = user_input; cookies["username"] = user_input; cookies.save(); st.rerun()
        st.stop()

# تنظیمات اصلی
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"])

if "messages_falcon" not in st.session_state: st.session_state.messages_falcon = []
if "persona" not in st.session_state: st.session_state.persona = "سارا (دوست‌داشتنی)"

user_dir = f"history/{st.session_state.username}"
if not os.path.exists(user_dir): os.makedirs(user_dir)

# سایدبار
with st.sidebar:
    st.write(f"کاربر: {st.session_state.username}")
    st.session_state.persona = st.selectbox("انتخاب شخصیت:", list(PERSONAS.keys()))
    selected_model = st.selectbox("مدل:", ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "meta-llama/llama-3.1-405b", "qwen/qwen-2.5-72b-instruct"])
    
    st.subheader("تاریخچه چت‌ها")
    chat_files = [f for f in os.listdir(user_dir) if f.endswith(".json")]
    for f in chat_files:
        if st.button(f):
            with open(os.path.join(user_dir, f), 'r') as file:
                st.session_state.messages_falcon = json.load(file)
            st.rerun()
    if st.button("شروع چت جدید"):
        st.session_state.messages_falcon = []
        st.rerun()

# لاجیک اصلی
st.title(f"Falcon AI - {st.session_state.persona}")
mode = st.radio("", ["👁️ تحلیل عکس", "🎨 تولید تصویر", "💬 چت عادی"], index=2, horizontal=True)

for msg in st.session_state.messages_falcon:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image_gen": st.image(msg["content"])
        else: st.markdown(msg["content"])

if prompt := st.chat_input("پیام..."):
    st.session_state.messages_falcon.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.status("در حال پردازش...", expanded=True) as status:
            if mode == "👁️ تحلیل عکس":
                res = analyze_image(st.file_uploader("عکس", type=["jpg"]), prompt, "auto")
            elif mode == "🎨 تولید تصویر":
                res = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?seed={random.randint(1,9999)}"
                st.image(res)
            else:
                sys_msg = {"role": "system", "content": f"{PERSONAS[st.session_state.persona]} پاسخ‌ها را فارسی بده."}
                res = (or_client if "/" in selected_model else groq_client).chat.completions.create(
                    model=selected_model, messages=[sys_msg] + st.session_state.messages_falcon[-6:], temperature=0.5
                ).choices[0].message.content
                st.markdown(res)
            status.update(label="پاسخ آماده شد!", state="complete", expanded=False)
    
    st.session_state.messages_falcon.append({"role": "assistant", "content": res, "type": "image_gen" if mode == "🎨 تولید تصویر" else "text"})
    
    # ذخیره‌سازی خودکار با تایم‌استمپ
    fname = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(os.path.join(user_dir, fname), 'w', encoding='utf-8') as file:
        json.dump(st.session_state.messages_falcon, file)
    st.rerun()
