import streamlit as st
from groq import Groq
from openai import OpenAI
import urllib.parse
import random 
import base64
import json
import os
from streamlit_cookies_manager import EncryptedCookieManager
import PyPDF2

# مدیریت کوکی
cookies = EncryptedCookieManager(prefix="falcon_ai", password="some_secret_password")
if not cookies.ready(): st.stop()

# تنظیم دایرکتوری‌ها
base_dir = os.path.dirname(os.path.abspath(__file__))
history_dir = os.path.join(base_dir, "history")
if not os.path.exists(history_dir): os.makedirs(history_dir)

st.set_page_config(page_title="Falcon AI", layout="wide")

# استایل‌ها
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    h1 { text-align: center !important; }
    div[data-testid="stRadio"] > div { display: flex !important; flex-direction: row !important; justify-content: center !important; gap: 10px !important; }
    [data-testid="stChatMessage"] { border: 2px solid #39FF14 !important; background-color: #1a1d23 !important; border-radius: 15px !important; padding: 10px !important; }
    </style>
""", unsafe_allow_html=True)

# سیستم شخصیت‌ها
persona_prompts = {
    "دستیار هوشمند": "تو یک دستیار همه فن حریف، دقیق و بسیار مودب هستی.",
    "برنامه‌نویس ارشد": "تو یک متخصص ارشد برنامه‌نویسی هستی که کدهای بهینه، تمیز و همراه با توضیح می‌نویسی.",
    "نویسنده خلاق": "تو یک نویسنده خوش‌ذوق هستی که با لحن ادبی و جذاب پاسخ می‌دهی.",
    "مربی انگیزشی": "تو یک مربی هستی که با انرژی بالا و جملات انگیزشی کاربر را راهنمایی می‌کنی.",
    "فیلسوف": "تو یک فیلسوف هستی که به مسائل از دیدگاهی عمیق، منطقی و گاهی انتزاعی نگاه می‌کنی."
}

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

vision_model_options = {
    "اتوماتیک": "auto", "Gemma 4": "google/gemma-4-31b-it", "Gemini Flash": "google/gemini-2.5-flash",
    "Llama 3.2 Vision": "meta-llama/llama-3.2-11b-vision-instruct"
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

user_path = os.path.join(history_dir, st.session_state.username)
if not os.path.exists(user_path): os.makedirs(user_path)

if "messages_falcon" not in st.session_state: 
    st.session_state.messages_falcon = []
    fpath = os.path.join(user_path, "chat_falcon.json")
    if os.path.exists(fpath):
        with open(fpath, 'r') as f: st.session_state.messages_falcon = json.load(f)

if "messages_sr" not in st.session_state: 
    st.session_state.messages_sr = []
    fpath = os.path.join(user_path, "chat_sr.json")
    if os.path.exists(fpath):
        with open(fpath, 'r') as f: st.session_state.messages_sr = json.load(f)

if "auth_sr" not in st.session_state: st.session_state.auth_sr = False
if "bot_mode" not in st.session_state: st.session_state.bot_mode = "FALCON AI"

def save_current_chat():
    fpath = os.path.join(user_path, f"chat_{'sr' if st.session_state.bot_mode == 'SR BOT' else 'falcon'}.json")
    with open(fpath, 'w') as f:
        json.dump(st.session_state.messages_sr if st.session_state.bot_mode == "SR BOT" else st.session_state.messages_falcon, f)

# سایدبار
with st.sidebar:
    st.write(f"کاربر: {st.session_state.username}")
    selected_persona = st.selectbox("شخصیت:", list(persona_prompts.keys()))
    new_mode = st.radio("بخش:", ["FALCON AI", "SR BOT"], index=0 if st.session_state.bot_mode=="FALCON AI" else 1)
    if new_mode != st.session_state.bot_mode: st.session_state.bot_mode = new_mode; st.rerun()
    selected_model = st.selectbox("مدل:", ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "meta-llama/llama-3.1-405b"])
    
    if st.button("شروع جدید"):
        if st.session_state.bot_mode == "SR BOT": st.session_state.messages_sr = []
        else: st.session_state.messages_falcon = []
        save_current_chat()
        st.rerun()

current_messages = st.session_state.messages_sr if st.session_state.bot_mode == "SR BOT" else st.session_state.messages_falcon

if st.session_state.bot_mode == "SR BOT" and not st.session_state.auth_sr:
    pwd = st.text_input("رمز سارا:", type="password")
    if st.button("ورود به سارا"):
        if pwd == "sara": st.session_state.auth_sr = True; st.rerun()
    st.stop()

st.title(st.session_state.bot_mode)
mode = st.radio("", ["👁️ تحلیل عکس", "📁 تحلیل فایل", "🎨 تولید تصویر", "💬 چت عادی"], index=3, horizontal=True)

model_key, uploaded_file, file_text = None, None, ""
if mode == "👁️ تحلیل عکس":
    model_name = st.selectbox("مدل تحلیل:", list(vision_model_options.keys()))
    model_key = vision_model_options[model_name]
    uploaded_file = st.file_uploader("عکس را آپلود کن:", type=["jpg", "jpeg", "png"])
elif mode == "📁 تحلیل فایل":
    uploaded_file = st.file_uploader("فایل را آپلود کن:", type=["pdf", "txt"])
    if uploaded_file: file_text = extract_file_text(uploaded_file)

for msg in current_messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image_gen": st.image(msg["content"])
        else: st.markdown(msg["content"])

if prompt := st.chat_input("پیام..."):
    current_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant"):
        res = ""
        sys_p = {"role": "system", "content": persona_prompts[selected_persona]}
        if mode == "👁️ تحلیل عکس" and uploaded_file is not None:
            res = analyze_image(uploaded_file, prompt, model_key)
        elif mode == "📁 تحلیل فایل" and file_text:
            prompt = f"متن فایل: {file_text[:2000]} \n\n سوال: {prompt}"
            res = or_client.chat.completions.create(model=selected_model, messages=[sys_p, {"role":"user", "content": prompt}]).choices[0].message.content
        elif mode == "🎨 تولید تصویر":
            url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?seed={random.randint(1,9999)}"
            st.image(url)
            res = url
            current_messages.append({"role": "assistant", "content": res, "type": "image_gen"})
        else:
            res = (or_client if "/" in selected_model else groq_client).chat.completions.create(
                model=selected_model, messages=[sys_p] + current_messages[-5:], temperature=0.2
            ).choices[0].message.content
        
        if mode != "🎨 تولید تصویر":
            st.markdown(res)
            current_messages.append({"role": "assistant", "content": res})
            
    save_current_chat()
    st.rerun()
