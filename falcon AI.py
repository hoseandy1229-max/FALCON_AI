import streamlit as st
from groq import Groq
from openai import OpenAI
import urllib.parse
import random 
import base64
import json
import sqlite3
import os
from datetime import datetime
from streamlit_cookies_manager import EncryptedCookieManager
from tavily import TavilyClient

# اتصال به دیتابیس SQLite
def init_db():
    conn = sqlite3.connect("falcon_ai.db", check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY)''')
    c.execute('''CREATE TABLE IF NOT EXISTS chats (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, chat_name TEXT, messages TEXT, FOREIGN KEY(username) REFERENCES users(username))''')
    conn.commit()
    return conn

conn = init_db()

# مدیریت کوکی
cookies = EncryptedCookieManager(prefix="𝑭𝒂𝒍𝒄𝒐𝒏 𝑨𝑰", password="some_secret_password")
if not cookies.ready(): st.stop()

# تنظیمات صفحه
st.set_page_config(page_title="Falcon AI", layout="wide", page_icon="logo.png")

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

def save_chat_to_db(username, chat_name, messages):
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO chats (username, chat_name, messages) VALUES (?, ?, ?)", 
              (username, chat_name, json.dumps(messages)))
    conn.commit()

def load_chat_from_db(username, chat_name):
    c = conn.cursor()
    c.execute("SELECT messages FROM chats WHERE username = ? AND chat_name = ?", (username, chat_name))
    res = c.fetchone()
    return json.loads(res[0]) if res else []

def get_user_chats(username):
    c = conn.cursor()
    c.execute("SELECT chat_name FROM chats WHERE username = ?", (username,))
    return [row[0] for row in c.fetchall()]

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
        if st.button("تایید"): 
            st.session_state.username = user_input
            cookies["username"] = user_input
            cookies.save()
            conn.cursor().execute("INSERT OR IGNORE INTO users VALUES (?)", (user_input,))
            conn.commit()
            st.rerun()
        st.stop()

# تنظیمات اصلی
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"])

if "messages_falcon" not in st.session_state: st.session_state.messages_falcon = []
if "messages_sr" not in st.session_state: st.session_state.messages_sr = []
if "auth_sr" not in st.session_state: st.session_state.auth_sr = False
if "bot_mode" not in st.session_state: st.session_state.bot_mode = "𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰"
if "current_chat" not in st.session_state: st.session_state.current_chat = f"Chat_{datetime.now().strftime('%Y%m%d%H%M%S')}"

# سایدبار
with st.sidebar:
    st.image("logo.png", use_column_width=True)
    st.write(f"کاربر: {st.session_state.username}")
    new_mode = st.radio("بخش:", ["𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰", "𝑺𝑹 𝑩𝑶𝑻"], index=0 if st.session_state.bot_mode=="𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰" else 1)
    if new_mode != st.session_state.bot_mode: st.session_state.bot_mode = new_mode; st.session_state.auth_sr = False; st.rerun()
    st.session_state.persona = st.selectbox("شخصیت:", list(PERSONAS.keys()))
    
    selected_model = st.selectbox("مدل:", ["llama-3.3-70b-versatile", "qwen/qwen-2.5-72b-instruct", "gryphe/mythomax-l2-13b", "mistralai/mistral-small-24b-instruct-2501"])

    with st.expander("📜 تاریخچه گفت و گوها"):
        chats = get_user_chats(st.session_state.username)
        for chat in chats:
            if st.button(chat, key=f"hist_{chat}"):
                st.session_state.current_chat = chat
                if st.session_state.bot_mode == "𝑺𝑹 𝑩𝑶𝑻": st.session_state.messages_sr = load_chat_from_db(st.session_state.username, chat)
                else: st.session_state.messages_falcon = load_chat_from_db(st.session_state.username, chat)
                st.rerun()
        if st.button("➕ شروع گفت و گوی جدید"):
            st.session_state.current_chat = f"Chat_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            if st.session_state.bot_mode == "𝑺𝑹 𝑩𝑶𝑻": st.session_state.messages_sr = []
            else: st.session_state.messages_falcon = []
            st.rerun()

    with st.expander(" 🔒 پنل مالکیت"):
        admin_pwd = st.text_input("رمز:", type="password")
        if admin_pwd == "admin123":
            all_users = [row[0] for row in conn.cursor().execute("SELECT username FROM users").fetchall()]
            sel_u = st.selectbox("کاربران:", all_users)
            user_chats = get_user_chats(sel_u)
            sel_f = st.selectbox("چت‌ها:", user_chats)
            if sel_f and st.button("مشاهده چت"):
                for msg in load_chat_from_db(sel_u, sel_f): st.write(f"**{msg['role']}:** {msg.get('content', '')}")
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
mode = st.radio("", ["👁️ تحلیل عکس", "🎨 تولید تصویر", "💬 چت عادی", "📝 برنامه‌نویسی"], index=2, horizontal=True)

# پردازش منطق برنامه و نمایش پیام‌ها (باقی مانده ساختار اصلی حفظ شد)
if mode == "📝 برنامه‌نویسی":
    st.subheader("💻 Falcon Code Studio")
    code_input = st.text_area("کد یا درخواست خود را وارد کنید:", height=200)
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("🛠️ دیباگ") or col2.button("🧪 تولید Unit Test") or col3.button("✨ تولید کد") or col4.button("🔄 تبدیل زبان"):
        with st.spinner("در حال پردازش..."):
            resp = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user", "content": code_input}]).choices[0].message.content
            st.code(resp)
            current_messages.append({"role": "assistant", "content": resp, "mode": "📝 برنامه‌نویسی"})
            save_chat_to_db(st.session_state.username, st.session_state.current_chat, current_messages)

for i, msg in enumerate(current_messages):
    if msg.get("mode", "💬 چت عادی") != mode: continue
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("𝑨𝑺𝑲 𝑭𝒂𝒍𝒄𝒐𝒏 𝑨𝑰"):
    current_messages.append({"role": "user", "content": prompt, "mode": mode})
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.status("در حال پردازش..."):
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=current_messages[-5:]).choices[0].message.content
            st.markdown(res)
    current_messages.append({"role": "assistant", "content": res, "mode": mode})
    save_chat_to_db(st.session_state.username, st.session_state.current_chat, current_messages)
    st.rerun()
