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

# مدیریت کوکی
cookies = EncryptedCookieManager(prefix="𝑭𝒂𝒍𝒄𝒐𝒏 𝑨𝑰", password="some_secret_password")
if not cookies.ready(): st.stop()

if not os.path.exists("history"): os.makedirs("history")
st.set_page_config(page_title="Falcon AI", layout="wide")

# کلاینت Tavily
tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])

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

# سیستم شخصیت‌ها
PERSONAS = {
    "دستیار (منظم)": "تو یک دستیار هوشمند، دقیق و بسیار منظم هستی.",
    "دانا (دانشمند)": "تو یک دانشمند هستی که با دقت و علمی پاسخ می‌دهی.",
    "سارا (دوست‌داشتنی)": "تو یک دوست صمیمی و مهربان هستی که با لحن گرم صحبت می‌کنی.",
    "استاد (سخت‌گیر)": "تو یک استاد سخت‌گیر هستی که به طور مختصر و فنی پاسخ می‌دهی.",
    "شوخ (طناز)": "تو همیشه با شوخی و طنز پاسخ می‌دهی.",
    "فیلسوف (متفکر)": "تو با دیدگاه فلسفی و عمیق به سوالات نگاه می‌کنی.",
    "نویسنده (خلاق)": "تو با ادبیاتی شاعرانه و خلاقانه پاسخ می‌دهی.",
    "کدنویس (منطقی)": "تو تمرکزت روی منطق و حل مسئله است و پاسخ‌های ساختاریافته می‌دهی.",
    "مربی (انگیزشی)": "تو پاسخ‌هایت پر از انرژی و انگیزه‌بخشی است."
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

def get_long_term_memory(user_dir, n=3):
    memory = []
    files = sorted([f for f in os.listdir(user_dir) if f.endswith(".json")], reverse=True)
    for f in files[:n]:
        with open(os.path.join(user_dir, f), 'r', encoding='utf-8') as file:
            try: data = json.load(file); memory.extend(data if isinstance(data, list) else [])
            except: pass
    return memory[-10:]

def search_web(query):
    if not query or query.strip() == "": return []
    try: return tavily.search(query=query, search_depth="advanced")["results"]
    except: return []

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
        st.title("ورود به 𝑭𝒂𝒍𝒄𝒐𝒏 𝑨𝑰")
        user_input = st.text_input("نام کاربری:")
        if st.button("تایید"): st.session_state.username = user_input; cookies["username"] = user_input; cookies.save(); st.rerun()
        st.stop()

# تنظیمات اصلی
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"])

# استفاده از دیکشنری برای تفکیک پیام‌ها به ازای هر مود
if "messages_dict" not in st.session_state: st.session_state.messages_dict = {}
if "auth_sr" not in st.session_state: st.session_state.auth_sr = False
if "bot_mode" not in st.session_state: st.session_state.bot_mode = "𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰"
if "persona" not in st.session_state: st.session_state.persona = "دستیار (منظم)"

user_dir = f"history/{st.session_state.username}"
if not os.path.exists(user_dir): os.makedirs(user_dir)

# سایدبار
with st.sidebar:
    st.write(f"کاربر: {st.session_state.username}")
    new_mode = st.radio("بخش:", ["𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰", "𝑺𝑹 𝑩𝑶𝑻"], index=0 if st.session_state.bot_mode=="𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰" else 1)
    if new_mode != st.session_state.bot_mode: st.session_state.bot_mode = new_mode; st.session_state.auth_sr = False; st.rerun()
    st.session_state.persona = st.selectbox("شخصیت:", list(PERSONAS.keys()))
    selected_model = st.selectbox("مدل:", ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "meta-llama/llama-3.1-405b", "qwen/qwen-2.5-72b-instruct"])

    with st.expander("📜 تاریخچه گفت و گوها"):
        history_files = sorted([f for f in os.listdir(user_dir) if f.endswith(".json")], reverse=True)
        for f in history_files:
            if st.button(f, key=f"hist_{f}"):
                with open(os.path.join(user_dir, f), 'r') as file: st.session_state.messages_dict = json.load(file)
                st.rerun()
        if st.button("➕ شروع گفت و گوی جدید"):
            st.session_state.messages_dict = {}; st.rerun()

    with st.expander(" 🔒 پنل مالکیت"):
        admin_pwd = st.text_input("رمز:", type="password")
        if admin_pwd == "admin123":
            sel_u = st.selectbox("کاربر:", os.listdir("history/"))
            if sel_u:
                sel_f = st.selectbox("چت:", os.listdir(f"history/{sel_u}"))
                if sel_f and st.button("مشاهده"):
                    with open(f"history/{sel_u}/{sel_f}", 'r') as file: st.write(json.load(file))

# رمز SR BOT
if st.session_state.bot_mode == "𝑺𝑹 𝑩𝑶𝑻" and not st.session_state.auth_sr:
    st.title("ورودی بخش خصوصی")
    pwd = st.text_input("رمز عبور:", type="password")
    if st.button("تایید رمز"):
        if pwd == "sara": st.session_state.auth_sr = True; st.rerun()
        else: st.error("رمز اشتباه است!")
    st.stop()

st.title(f"{st.session_state.bot_mode} - {PERSONA_EMOJIS.get(st.session_state.persona)} {st.session_state.persona}")
mode = st.radio("", ["👁️ تحلیل عکس", "🎨 تولید تصویر", "💬 چت عادی", "📝 برنامه‌نویسی"], index=2, horizontal=True)

# تفکیک پیام‌ها بر اساس مود
if mode not in st.session_state.messages_dict: st.session_state.messages_dict[mode] = []
current_messages = st.session_state.messages_dict[mode]

# نمایش پیام‌ها
for i, msg in enumerate(current_messages):
    av = PERSONA_EMOJIS.get(st.session_state.persona) if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=av):
        if msg.get("type") == "image_gen": st.image(msg["content"])
        else: st.markdown(msg["content"])

# حالت برنامه‌نویسی (همون حالت قبلی با دکمه‌ها)
if mode == "📝 برنامه‌نویسی":
    st.subheader("💻 Falcon Code Studio")
    code_input = st.text_area("کد یا درخواست خود را وارد کنید:", height=200)
    col1, col2, col3, col4 = st.columns(4)
    btn_fix = col1.button("🛠️ دیباگ"); btn_test = col2.button("🧪 Unit Test"); btn_gen = col3.button("✨ تولید"); btn_trans = col4.button("🔄 تبدیل")
    if btn_fix or btn_test or btn_gen or btn_trans:
        task = "اصلاح" if btn_fix else "تولید تست" if btn_test else "تولید" if btn_gen else "تبدیل"
        resp = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user", "content": f"{task}: {code_input}"}]).choices[0].message.content
        current_messages.append({"role": "assistant", "content": resp}); st.rerun()
elif mode == "👁️ تحلیل عکس":
    uploaded_file = st.file_uploader("عکس:", type=["jpg", "png"])
    if uploaded_file and (prompt := st.chat_input("توضیح عکس:")):
        res = analyze_image(uploaded_file, prompt, "auto")
        current_messages.append({"role": "assistant", "content": res}); st.rerun()

# چت عادی و تولید تصویر
if mode in ["💬 چت عادی", "🎨 تولید تصویر"] and (prompt := st.chat_input("𝑨𝑺𝑲 𝑭𝒂𝒍𝒄𝒐𝒏 𝑨𝑰")):
    current_messages.append({"role": "user", "content": prompt})
    if mode == "🎨 تولید تصویر":
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}"
        current_messages.append({"role": "assistant", "content": url, "type": "image_gen"})
    else:
        res = (or_client if "/" in selected_model else groq_client).chat.completions.create(model=selected_model, messages=[{"role":"user","content":prompt}]).choices[0].message.content
        current_messages.append({"role": "assistant", "content": res})
    st.rerun()

# ذخیره
fname = f"{st.session_state.bot_mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(os.path.join(user_dir, fname), 'w', encoding='utf-8') as file: json.dump(st.session_state.messages_dict, file)
