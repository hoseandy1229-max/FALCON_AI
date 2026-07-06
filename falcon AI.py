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

# مدیریت دیتابیس
def init_db():
    conn = sqlite3.connect("falcon_ai.db", check_same_thread=False)
    c = conn.cursor()
    # ایجاد جدول کاربران
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY)''')
    # اضافه کردن ستون summary اگر وجود ندارد
    try:
        c.execute('''ALTER TABLE users ADD COLUMN summary TEXT''')
    except sqlite3.OperationalError:
        pass 
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, filename TEXT, messages TEXT)''')
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

def update_memory_summary(current_messages, existing_summary):
    if len(current_messages) < 6: return existing_summary
    prompt = f"خلاصه ای بسیار کوتاه و مفید از این گفتگو برای درک نیازهای کاربر ارائه بده:\n{str(current_messages[-6:])}"
    return groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}]).choices[0].message.content

def get_client_and_model(model_name):
    if "/" in model_name: return or_client, model_name
    return groq_client, model_name

def get_long_term_memory(username, n=3):
    c = conn.cursor()
    c.execute("SELECT messages FROM chat_history WHERE username = ? ORDER BY id DESC LIMIT ?", (username, n))
    results = c.fetchall()
    memory = []
    for row in results:
        try: memory.extend(json.loads(row[0]))
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
        if st.button("تایید"): 
            st.session_state.username = user_input; cookies["username"] = user_input; cookies.save()
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO users (username, summary) VALUES (?, ?)", (user_input, ""))
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
if "persona" not in st.session_state: st.session_state.persona = "دستیار (منظم)"
if "user_pref" not in st.session_state: st.session_state.user_pref = ""
if "curr_chat" not in st.session_state: st.session_state.curr_chat = None

# بازیابی خلاصه از دیتابیس
c = conn.cursor()
c.execute("SELECT summary FROM users WHERE username = ?", (st.session_state.username,))
result_sum = c.fetchone()
st.session_state.memory_summary = result_sum[0] if result_sum else ""

# سایدبار
with st.sidebar:
    st.image("logo.png", use_column_width=True)
    st.write(f"کاربر: {st.session_state.username}")
    new_mode = st.radio("بخش:", ["𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰", "𝑺𝑹 𝑩𝑶𝑻"], index=0 if st.session_state.bot_mode=="𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰" else 1)
    if new_mode != st.session_state.bot_mode: st.session_state.bot_mode = new_mode; st.session_state.auth_sr = False; st.rerun()
    st.session_state.persona = st.selectbox("شخصیت:", list(PERSONAS.keys()))
    
    selected_model = st.selectbox("مدل:", [
        "llama-3.3-70b-versatile", 
        "qwen/qwen-2.5-72b-instruct", 
        "gryphe/mythomax-l2-13b",
        "mistralai/mistral-small-24b-instruct-2501"
    ])

    with st.expander("📜 تاریخچه گفت و گوها"):
        c = conn.cursor()
        c.execute("SELECT DISTINCT filename FROM chat_history WHERE username = ?", (st.session_state.username,))
        history_files = [row[0] for row in c.fetchall()]
        for f in history_files:
            if st.button(f, key=f"hist_{f}"):
                st.session_state.curr_chat = f
                c.execute("SELECT messages FROM chat_history WHERE username = ? AND filename = ?", (st.session_state.username, f))
                data = json.loads(c.fetchone()[0])
                if st.session_state.bot_mode == "𝑺𝑹 𝑩𝑶𝑻": st.session_state.messages_sr = data
                else: st.session_state.messages_falcon = data
                st.rerun()
        if st.button("➕ شروع گفت و گوی جدید"):
            st.session_state.curr_chat = None
            if st.session_state.bot_mode == "𝑺𝑹 𝑩𝑶𝑻": st.session_state.messages_sr = []
            else: st.session_state.messages_falcon = []
            st.rerun()

    with st.expander(" 🔒 پنل مالکیت"):
        admin_pwd = st.text_input("رمز:", type="password")
        if admin_pwd == "admin123":
            c = conn.cursor()
            c.execute("SELECT username FROM users UNION SELECT DISTINCT username FROM chat_history")
            all_users = [row[0] for row in c.fetchall()]
            sel_u = st.selectbox("کاربر:", all_users)
            if sel_u:
                if st.button(f"🚫 حذف کامل کاربر: {sel_u}"):
                    c.execute("DELETE FROM users WHERE username = ?", (sel_u,))
                    c.execute("DELETE FROM chat_history WHERE username = ?", (sel_u,))
                    conn.commit(); st.rerun()
                c.execute("SELECT DISTINCT filename FROM chat_history WHERE username = ?", (sel_u,))
                sel_f = st.selectbox("چت:", [row[0] for row in c.fetchall()])
                if sel_f:
                    if st.button(f"🗑️ حذف چت: {sel_f}"):
                        c.execute("DELETE FROM chat_history WHERE username = ? AND filename = ?", (sel_u, sel_f))
                        conn.commit(); st.rerun()
                    if st.button("مشاهده محتوا"):
                        c.execute("SELECT messages FROM chat_history WHERE username = ? AND filename = ?", (sel_u, sel_f))
                        for msg in json.loads(c.fetchone()[0]): st.write(f"**{msg['role']}:** {msg.get('content', '')}")
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
        system_msg = f"تو یک متخصص برنامه‌نویسی هستی. وظیفه تو {task} است. فقط کد خروجی بده."
        with st.spinner(f"در حال {task}..."):
            resp = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system", "content": system_msg}, {"role":"user", "content": code_input}]).choices[0].message.content
            st.code(resp, language=lang_dest if btn_trans else lang_src)
            current_messages.append({"role": "assistant", "content": f"**{task} خروجی:**\n\n{resp}", "mode": "📝 برنامه‌نویسی"})
elif mode == "👁️ تحلیل عکس":
    model_name = st.selectbox("مدل تحلیل:", list(vision_model_options.keys()))
    model_key = vision_model_options[model_name]
    uploaded_file = st.file_uploader("عکس را آپلود کن:", type=["jpg", "jpeg", "png"])

# نمایش پیام‌ها
for i, msg in enumerate(current_messages):
    if msg.get("mode", "💬 چت عادی") != mode: continue
    av = PERSONA_EMOJIS.get(st.session_state.persona) if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=av):
        if msg.get("type") == "image_gen": st.image(msg["content"])
        else: st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("type") != "image_gen":
            col1, col2 = st.columns([0.5, 0.5])
            with col1: 
                if st.button("👍", key=f"like_{i}"): st.session_state.user_pref += f" [لایک: {msg['content'][:15]}]"
            with col2: 
                if st.button("👎", key=f"dislike_{i}"): st.session_state.user_pref += f" [دیس: {msg['content'][:15]}]"

if prompt := st.chat_input("𝑨𝑺𝑲 𝑭𝒂𝒍𝒄𝒐𝒏 𝑨𝑰"):
    current_messages.append({"role": "user", "content": prompt, "mode": mode})
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant", avatar=PERSONA_EMOJIS.get(st.session_state.persona)):
        if mode == "👁️ تحلیل عکس" and uploaded_file is not None:
            with st.status("در حال تجزیه و تحلیل...", expanded=True) as status:
                res = analyze_image(uploaded_file, prompt, model_key)
                st.markdown(res)
            current_messages.append({"role": "assistant", "content": res, "mode": mode})
        elif mode == "🎨 تولید تصویر":
            with st.status("در حال تولید تصویر...", expanded=True) as status:
                tr_prompt = or_client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"system","content":"Translate to english, output ONLY the prompt"}, {"role":"user","content":prompt}]).choices[0].message.content
                url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(tr_prompt)}?seed={random.randint(1,9999)}"
                st.image(url)
            current_messages.append({"role": "assistant", "content": url, "type": "image_gen", "mode": mode})
        elif mode == "💬 چت عادی":
            with st.status("در حال پردازش...", expanded=True) as status:
                if len(current_messages) % 5 == 0:
                    st.session_state.memory_summary = update_memory_summary(current_messages, st.session_state.memory_summary)
                    c = conn.cursor()
                    c.execute("UPDATE users SET summary = ? WHERE username = ?", (st.session_state.memory_summary, st.session_state.username))
                    conn.commit()
                memory = get_long_term_memory(st.session_state.username)
                search_results = search_web(prompt)
                sys_prompt = f"شخصیت شما: {PERSONAS[st.session_state.persona]}. حافظه اصلی: {st.session_state.memory_summary}. جستجو: {str(search_results)[:500]}. پاسخ فارسی بده."
                clean_history = [{"role": m["role"], "content": m["content"]} for m in current_messages[-3:] if "role" in m and "content" in m]
                messages_to_send = [{"role": "system", "content": sys_prompt}] + clean_history
                client, model = get_client_and_model(selected_model)
                res = client.chat.completions.create(model=model, messages=messages_to_send, temperature=0.2).choices[0].message.content
                st.markdown(res)
            current_messages.append({"role": "assistant", "content": res, "mode": mode})
    
    if not st.session_state.curr_chat:
        st.session_state.curr_chat = f"{st.session_state.bot_mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO chat_history (username, filename, messages) VALUES (?, ?, ?)", (st.session_state.username, st.session_state.curr_chat, json.dumps(current_messages)))
    conn.commit()
    st.rerun()
