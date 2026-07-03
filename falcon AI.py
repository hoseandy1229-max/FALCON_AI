import streamlit as st
from groq import Groq
from openai import OpenAI
import urllib.parse
import random 
import base64
import json
import os
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
    div[data-testid="stRadio"] > div { display: flex !important; flex-direction: row !important; justify-content: center !important; gap: 10px !important; }
    div[data-testid="stRadio"] label { font-size: 14px !important; padding: 5px !important; }
    [data-testid="stChatMessage"] { border: 2px solid #39FF14 !important; background-color: #1a1d23 !important; border-radius: 15px !important; padding: 10px !important; }
    </style>
""", unsafe_allow_html=True)

# تنظیمات کلاینت‌ها
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"])

# مدل‌های تحلیل تصویر
vision_model_options = {
    "اتوماتیک (هوشمند)": "auto",
    "Gemma 4": "google/gemma-4-31b-it",
    "Nemotron": "nvidia/nemotron-3-nano-omni",
    "Gemini Flash": "google/gemini-2.5-flash",
    "Llama 3.2 Vision": "meta-llama/llama-3.2-11b-vision-instruct",
    "Qwen VL": "qwen/qwen-2-vl-72b-instruct",
    "Pixtral": "mistralai/pixtral-12b"
}

def analyze_image(uploaded_file, user_prompt, model_to_use):
    bytes_data = uploaded_file.getvalue()
    base64_image = base64.b64encode(bytes_data).decode('utf-8')
    target_models = [m for m in vision_model_options.values() if m != "auto"] if model_to_use == "auto" else [model_to_use]
    for model in target_models:
        try:
            response = or_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": user_prompt or "این عکس را تحلیل کن"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}]
            )
            return response.choices[0].message.content
        except: continue
    return "خطا: مدل‌های تحلیل در حال حاضر در دسترس نیستند."

# شروع برنامه
if "username" not in st.session_state:
    if "username" in cookies: st.session_state.username = cookies["username"]
    else:
        st.title("ورود به Falcon AI")
        user_input = st.text_input("نام کاربری:")
        if st.button("تایید"):
            st.session_state.username = user_input; cookies["username"] = user_input; cookies.save(); st.rerun()
        st.stop()

if "bot_mode" not in st.session_state: st.session_state.bot_mode = "FALCON AI"
user_dir = f"history/{st.session_state.username}"
if not os.path.exists(user_dir): os.makedirs(user_dir)

with st.sidebar:
    new_mode = st.radio("بخش:", ["FALCON AI", "SR BOT"], index=0 if st.session_state.bot_mode=="FALCON AI" else 1)
    if new_mode != st.session_state.bot_mode: st.session_state.bot_mode = new_mode; st.rerun()
    selected_model = st.selectbox("مدل:", ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "meta-llama/llama-3.1-405b", "qwen/qwen-2.5-72b-instruct"])

current_messages = st.session_state.messages_sr if st.session_state.bot_mode == "SR BOT" else st.session_state.messages_falcon

st.title(st.session_state.bot_mode)
with st.container():
    st.markdown("<h3 style='text-align: center;'>حالت کاری:</h3>", unsafe_allow_html=True)
    mode = st.radio("", ["👁️ تحلیل عکس", "🎨 تولید تصویر", "💬 چت عادی"], horizontal=True, label_visibility="collapsed")

uploaded_file = None
model_key = None
if mode == "👁️ تحلیل عکس":
    model_name = st.selectbox("انتخاب مدل تحلیل:", list(vision_model_options.keys()))
    model_key = vision_model_options[model_name]
    uploaded_file = st.file_uploader("عکس را آپلود کن:", type=["jpg", "jpeg", "png"])

for msg in current_messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image_gen": st.image(msg["content"])
        else: st.markdown(msg["content"])

if prompt := st.chat_input("پیام..."):
    current_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant"):
        if mode == "👁️ تحلیل عکس" and uploaded_file is not None:
            res = analyze_image(uploaded_file, prompt, model_key)
            st.markdown(res)
            current_messages.append({"role": "assistant", "content": res})
        elif mode == "🎨 تولید تصویر":
            url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?seed={random.randint(1,9999)}"
            st.image(url)
            current_messages.append({"role": "assistant", "content": url, "type": "image_gen"})
        else:
            res = (or_client if "/" in selected_model else groq_client).chat.completions.create(
                model=selected_model, messages=[{"role":"system","content":"فارسی پاسخ بده"}] + current_messages[-5:], temperature=0.2
            ).choices[0].message.content
            st.markdown(res)
            current_messages.append({"role": "assistant", "content": res})
    
    with open(os.path.join(user_dir, f"{st.session_state.bot_mode}_{st.session_state.username}.json"), 'w') as file: json.dump(current_messages, file)
    st.rerun()
