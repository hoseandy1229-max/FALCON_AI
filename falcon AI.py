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
from tavily import TavilyClient

# مدیریت کوکی‌ها
cookies = EncryptedCookieManager(prefix="𝑭𝒂𝒍𝒄𝒐𝒏 𝑨𝑰", password="some_secret_password")
if not cookies.ready(): st.stop()
if not os.path.exists("history"): os.makedirs("history")
st.set_page_config(page_title="Falcon AI", layout="wide", page_icon="logo.png")

# کلاینت‌های اتصال
tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"])

# استایل‌های CSS
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    h1 { text-align: center !important; }
    div[data-testid="stRadio"] > div { display: flex !important; flex-direction: row !important; justify-content: center !important; gap: 10px !important; }
    div[data-testid="stRadio"] label { font-size: 14px !important; padding: 5px !important; }
    [data-testid="stChatMessage"] { border: 2px solid #39FF14 !important; background-color: #1a1d23 !important; border-radius: 15px !important; padding: 10px !important; }
    </style>
""", unsafe_allow_html=True)

# سیستم پرسونا
PERSONAS = {
    "دستیار (منظم)": "تو یک دستیار هوشمند و دقیق هستی.",
    "دانا (دانشمند)": "تو یک دانشمند هستی با دانش عمیق.",
    "سارا (دوست‌داشتنی)": "تو یک دوست صمیمی و بسیار مهربان هستی.",
    "استاد (سخت‌گیر)": "تو یک استاد سخت‌گیر و فنی پاسخ می‌دهی.",
    "شوخ (طناز)": "تو همیشه با شوخی و طنز پاسخ می‌دهی.",
    "فیلسوف (متفکر)": "تو با نگاهی فلسفی پاسخ می‌دهی.",
    "نویسنده (خلاق)": "تو با ادبیاتی شاعرانه پاسخ می‌دهی.",
    "کدنویس (منطقی)": "تو متخصص حل مسئله و منطق برنامه‌نویسی هستی.",
    "مربی (انگیزشی)": "تو پاسخ‌های پرانرژی و انگیزه بخش داری."
}

PERSONA_EMOJIS = {
    "دستیار (منظم)": "🤖", "دانا (دانشمند)": "🧬", "سارا (دوست‌داشتنی)": "🌸",
    "استاد (سخت‌گیر)": "🎓", "شوخ (طناز)": "🤡", "فیلسوف (متفکر)": "🧠",
    "نویسنده (خلاق)": "✍️", "کدنویس (منطقی)": "💻", "مربی (انگیزشی)": "🔥"
}

vision_model_options = {
    "اتوماتیک": "auto", "Gemma 4": "google/gemma-4-31b-it", "Nemotron": "nvidia/nemotron-3-nano-omni",
    "Gemini Flash": "google/gemini-2.5-flash", "Llama 3.2 Vision": "meta-llama/llama-3.2-11b-vision-instruct",
    "Qwen VL": "qwen/qwen-2-vl-72b-instruct", "Pixtral": "mistralai/pixtral-12b"
}

# توابع عملیاتی
def get_client_and_model(model_name):
    if "/" in model_name: return or_client, model_name
    return groq_client, model_name

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

# احراز هویت اولیه
if "username" not in st.session_state:
    if "username" in cookies: st.session_state.username = cookies["username"]
    else:
        st.title("ورود به 𝑭𝒂𝒍𝒄𝒐𝒏 𝑨𝑰")
        user_input = st.text_input("نام کاربری را وارد کن:")
        if st.button("تایید ورود"): st.session_state.username = user_input; cookies["username"] = user_input; cookies.save(); st.rerun()
        st.stop()

# وضعیت‌ها
if "messages_falcon" not in st.session_state: 
    if os.path.exists(f"history/{st.session_state.username}.json"):
        with open(f"history/{st.session_state.username}.json", "r") as f: st.session_state.messages_falcon = json.load(f)
    else: st.session_state.messages_falcon = []

if "messages_sr" not in st.session_state: st.session_state.messages_sr = []
if "auth_sr" not in st.session_state: st.session_state.auth_sr = False
if "bot_mode" not in st.session_state: st.session_state.bot_mode = "𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰"
if "persona" not in st.session_state: st.session_state.persona = "دستیار (منظم)"

# سایدبار
with st.sidebar:
    st.image("logo.png", use_column_width=True)
    st.write(f"کاربر فعلی: {st.session_state.username}")
    new_mode = st.radio("بخش:", ["𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰", "𝑺𝑹 𝑩𝑶𝑻"], index=0)
    if new_mode != st.session_state.bot_mode: st.session_state.bot_mode = new_mode; st.session_state.auth_sr = False; st.rerun()
    st.session_state.persona = st.selectbox("پرسونا:", list(PERSONAS.keys()))
    selected_model = st.selectbox("مدل:", ["llama-3.3-70b-versatile", "qwen/qwen-2.5-72b-instruct", "gryphe/mythomax-l2-13b", "mistralai/mistral-small-24b-instruct-2501"])

    with st.expander("📜 تاریخچه"):
        if st.button("➕ جدید"):
            if st.session_state.bot_mode == "𝑺𝑹 𝑩𝑶𝑻": st.session_state.messages_sr = []
            else: st.session_state.messages_falcon = []
            st.rerun()
    
    with st.expander(" 🔒 پنل مدیریت"):
        admin_pwd = st.text_input("رمز:", type="password")
        if admin_pwd == "admin123":
            st.subheader("کاربران لاگین شده")
            for f in os.listdir("history"): st.write(f"- {f.replace('.json', '')}")
            st.subheader("فایل‌های چت")
            for f_name in os.listdir("history"):
                if f_name.endswith(".json"):
                    if st.button(f"مشاهده: {f_name}"):
                        with open(f"history/{f_name}", "r") as f: st.json(json.load(f))
        elif admin_pwd: st.error("رمز اشتباه")

# بخش خصوصی
if st.session_state.bot_mode == "𝑺𝑹 𝑩𝑶𝑻" and not st.session_state.auth_sr:
    st.title("دسترسی خصوصی")
    pwd = st.text_input("رمز:", type="password")
    if st.button("تایید"):
        if pwd == "sara": st.session_state.auth_sr = True; st.rerun()
        else: st.error("اشتباه!")
    st.stop()

current_messages = st.session_state.messages_sr if st.session_state.bot_mode == "𝑺𝑹 𝑩𝑶𝑻" else st.session_state.messages_falcon

st.title(f"{st.session_state.bot_mode} - {PERSONA_EMOJIS.get(st.session_state.persona)} {st.session_state.persona}")
with st.container():
    mode = st.radio("", ["👁️ تحلیل", "🎨 تصویر", "💬 چت", "📝 کد"], index=2, horizontal=True)

model_key, uploaded_file = None, None

if mode == "📝 کد":
    code_input = st.text_area("کد:", height=200)
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("🛠️ دیباگ"):
        resp = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user", "content": f"Fix: {code_input}"}]).choices[0].message.content
        st.code(resp); current_messages.append({"role": "assistant", "content": resp})

elif mode == "👁️ تحلیل":
    model_name = st.selectbox("مدل:", list(vision_model_options.keys()))
    model_key = vision_model_options[model_name]
    uploaded_file = st.file_uploader("آپلود:", type=["jpg", "png"])

for msg in current_messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("پیام..."):
    current_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant"):
        if mode == "👁️ تحلیل" and uploaded_file:
            res = analyze_image(uploaded_file, prompt, model_key)
        elif mode == "🎨 تصویر":
            trans_p = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user", "content": f"Translate: {prompt}"}]).choices[0].message.content
            res = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(trans_p)}?seed={random.randint(1,999)}"
            st.image(res)
        else:
            client, model = get_client_and_model(selected_model)
            res = client.chat.completions.create(model=model, messages=[{"role": "system", "content": PERSONAS[st.session_state.persona]}, {"role": "user", "content": prompt}]).choices[0].message.content
            st.markdown(res)
        current_messages.append({"role": "assistant", "content": res})
        with open(f"history/{st.session_state.username}.json", "w") as f: json.dump(current_messages, f)
    st.rerun()

# [LINE_220]
# [LINE_221]
# [LINE_222]
# [LINE_223]
# [LINE_224]
# [LINE_225]
