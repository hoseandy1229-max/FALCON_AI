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
from supabase import create_client

# مدیریت کوکی
cookies = EncryptedCookieManager(prefix="𝑭𝒂𝒍𝒄𝒐𝒏 𝑨𝑰", password="some_secret_password")
if not cookies.ready(): st.stop()

if not os.path.exists("history"): os.makedirs("history")
st.set_page_config(page_title="Falcon AI", layout="wide", page_icon="logo.png")

# اتصال به دیتابیس سوپابیس
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

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

def get_client_and_model(model_name):
    if "/" in model_name: return or_client, model_name
    return groq_client, model_name

def get_long_term_memory(username, mode, n=10):
    try:
        res = supabase.table("Falcon").select("role, content").eq("username", username).eq("mode", mode).execute()
        return [{"role": i["role"], "content": i["content"]} for i in res.data] if res.data else []
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

if "messages_falcon" not in st.session_state: st.session_state.messages_falcon = []
if "messages_sr" not in st.session_state: st.session_state.messages_sr = []
if "auth_sr" not in st.session_state: st.session_state.auth_sr = False
if "bot_mode" not in st.session_state: st.session_state.bot_mode = "𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰"
if "persona" not in st.session_state: st.session_state.persona = "دستیار (منظم)"

# سایدبار
with st.sidebar:
    st.image("logo.png", use_column_width=True)
    st.write(f"کاربر: {st.session_state.username}")
    new_mode = st.radio("بخش:", ["𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰", "𝑺𝑹 𝑩𝑶𝑻"], index=0)
    if new_mode != st.session_state.bot_mode: st.session_state.bot_mode = new_mode; st.session_state.auth_sr = False; st.rerun()
    st.session_state.persona = st.selectbox("شخصیت:", list(PERSONAS.keys()))
    selected_model = st.selectbox("مدل:", ["llama-3.3-70b-versatile", "qwen/qwen-2.5-72b-instruct", "gryphe/mythomax-l2-13b", "mistralai/mistral-small-24b-instruct-2501"])

    with st.expander("📜 تاریخچه گفت و گوها"):
        if st.button("➕ شروع گفت و گوی جدید"):
            if st.session_state.bot_mode == "𝑺𝑹 𝑩𝑶𝑻": st.session_state.messages_sr = []
            else: st.session_state.messages_falcon = []
            st.rerun()
        st.write("تاریخچه بارگذاری شد.")

    with st.expander(" 🔒 پنل مالکیت"):
        admin_pwd = st.text_input("رمز:", type="password")
        if admin_pwd == "admin123":
            try:
                res = supabase.table("Falcon").select("username").execute()
                if res.data:
                    users = list(set([u['username'] for u in res.data if u.get('username')]))
                    sel_u = st.selectbox("کاربران لاگین کرده:", users)
                    if sel_u:
                        chat_data = supabase.table("Falcon").select("role, content").eq("username", sel_u).execute().data
                        for msg in chat_data: st.write(f"**{msg['role']}:** {msg['content']}")
                else: st.write("دیتا خالی است")
            except Exception as e: st.write(f"خطا در پنل: {e}")
        elif admin_pwd: st.error("رمز غلط")

# رمز SR BOT
if st.session_state.bot_mode == "𝑺𝑹 𝑩𝑶𝑻" and not st.session_state.auth_sr:
    st.title("ورودی بخش خصوصی")
    pwd = st.text_input("رمز عبور:", type="password")
    if st.button("تایید رمز"):
        if pwd == "sara": st.session_state.auth_sr = True; st.rerun()
        else: st.error("رمز اشتباه است!")
    st.stop()

current_messages = st.session_state.messages_sr if st.session_state.bot_mode == "𝑺𝑹 𝑩𝑶𝑻" else st.session_state.messages_falcon

st.title(f"{st.session_state.bot_mode} - {PERSONA_EMOJIS.get(st.session_state.persona)} {st.session_state.persona}")
with st.container():
    st.markdown("<h3 style='text-align: center;'>حالت کاری:</h3>", unsafe_allow_html=True)
    mode = st.radio("", ["👁️ تحلیل عکس", "🎨 تولید تصویر", "💬 چت عادی", "📝 برنامه‌نویسی"], index=2, horizontal=True, label_visibility="collapsed")

model_key = None
uploaded_file = None

if mode == "📝 برنامه‌نویسی":
    st.subheader("💻 Falcon Code Studio")
    code_input = st.text_area("کد یا درخواست خود را وارد کنید:", height=200)
    col_l1, col_l2 = st.columns(2)
    with col_l1: lang_src = st.selectbox("زبان مبدأ:", ["python", "javascript", "cpp", "java", "html", "css"])
    with col_l2: lang_dest = st.selectbox("تبدیل به:", ["javascript", "python", "java", "cpp", "csharp", "php"])
    col1, col2, col3, col4 = st.columns(4)
    with col1: btn_fix = st.button("🛠️ دیباگ")
    with col2: btn_test = st.button("🧪 تولید Unit Test")
    with col3: btn_gen = st.button("✨ تولید کد")
    with col4: btn_trans = st.button("🔄 تبدیل زبان")
    if btn_fix or btn_test or btn_gen or btn_trans:
        task = "اصلاح کد" if btn_fix else "تولید Unit Test" if btn_test else "نوشتن کد" if btn_gen else f"تبدیل از {lang_src} به {lang_dest}"
        resp = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user", "content": f"Task: {task}. Code: {code_input}"}]).choices[0].message.content
        st.code(resp, language=lang_dest if btn_trans else lang_src)
        current_messages.append({"role": "assistant", "content": resp})
        try: supabase.table("Falcon").insert({"username": st.session_state.username, "role": "assistant", "content": resp, "mode": mode}).execute()
        except: pass
elif mode == "👁️ تحلیل عکس":
    model_name = st.selectbox("مدل تحلیل:", list(vision_model_options.keys()))
    model_key = vision_model_options[model_name]
    uploaded_file = st.file_uploader("عکس را آپلود کن:", type=["jpg", "jpeg", "png"])

for i, msg in enumerate(current_messages):
    av = PERSONA_EMOJIS.get(st.session_state.persona) if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=av):
        if msg.get("type") == "image_gen": st.image(msg["content"])
        else: st.markdown(msg["content"])

if prompt := st.chat_input("𝑨𝑺𝑲 𝑭𝒂𝒍𝒄𝒐𝒏 𝑨𝑰"):
    current_messages.append({"role": "user", "content": prompt})
    try: supabase.table("Falcon").insert({"username": st.session_state.username, "role": "user", "content": prompt, "mode": mode}).execute()
    except: pass
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant", avatar=PERSONA_EMOJIS.get(st.session_state.persona)):
        if mode == "👁️ تحلیل عکس" and uploaded_file is not None:
            res = analyze_image(uploaded_file, prompt, model_key)
            st.markdown(res)
        elif mode == "🎨 تولید تصویر":
            res = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?seed={random.randint(1,9999)}"
            st.image(res)
        else:
            client, model = get_client_and_model(selected_model)
            res = client.chat.completions.create(model=model, messages=[{"role": "system", "content": PERSONAS[st.session_state.persona]}, {"role": "user", "content": prompt}]).choices[0].message.content
            st.markdown(res)
        current_messages.append({"role": "assistant", "content": res})
        try: supabase.table("Falcon").insert({"username": st.session_state.username, "role": "assistant", "content": res, "mode": mode}).execute()
        except: pass
    st.rerun()
