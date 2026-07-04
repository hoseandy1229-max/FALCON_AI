```python
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
    [data-testid="stChatMessage"] { border: 2px solid #39FF14 !important; background-color: #1a1d23 !important; border-radius: 15px !important; padding: 10px !important; }
    .action-row { display: flex; flex-direction: row; gap: 5px; margin-top: 5px; }
    </style>
""", unsafe_allow_html=True)

# سیستم شخصیت‌ها
PERSONAS = {
    "دستیار (منظم)": "📋", "دانا (دانشمند)": "🔬", "سارا (دوست‌داشتنی)": "💖",
    "استاد (سخت‌گیر)": "🎓", "شوخ (طناز)": "🤡", "فیلسوف (متفکر)": "🤔",
    "نویسنده (خلاق)": "✍️", "کدنویس (منطقی)": "💻", "مربی (انگیزشی)": "🚀"
}

PERSONA_PROMPTS = {
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
            try: memory.extend(json.load(file))
            except: continue
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

groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"])

if "messages_falcon" not in st.session_state: st.session_state.messages_falcon = []
if "messages_sr" not in st.session_state: st.session_state.messages_sr = []
if "auth_sr" not in st.session_state: st.session_state.auth_sr = False
if "bot_mode" not in st.session_state: st.session_state.bot_mode = "𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰"
if "persona" not in st.session_state: st.session_state.persona = "دستیار (منظم)"
if "user_pref" not in st.session_state: st.session_state.user_pref = ""

user_dir = f"history/{st.session_state.username}"
if not os.path.exists(user_dir): os.makedirs(user_dir)

# سایدبار
with st.sidebar:
    st.write(f"کاربر: {st.session_state.username}")
    new_mode = st.radio("بخش:", ["𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰", "𝑺𝑹 𝑩𝑶𝑻"], index=0 if st.session_state.bot_mode=="𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰" else 1)
    if new_mode != st.session_state.bot_mode: st.session_state.bot_mode = new_mode; st.session_state.auth_sr = False; st.rerun()
    st.session_state.persona = st.selectbox("شخصیت:", list(PERSONAS.keys()))
    selected_model = st.selectbox("مدل:", ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "meta-llama/llama-3.1-405b", "qwen/qwen-2.5-72b-instruct"])
    
    st.subheader("تاریخچه")
    for f in [f for f in os.listdir(user_dir) if f.endswith(".json")]:
        if st.button(f):
            with open(os.path.join(user_dir, f), 'r') as file:
                data = json.load(file)
                if st.session_state.bot_mode == "𝑺𝑹 𝑩𝑶𝑻": st.session_state.messages_sr = data
                else: st.session_state.messages_falcon = data
            st.rerun()
    if st.button("گفت و گو جدید"):
        if st.session_state.bot_mode == "𝑺𝑹 𝑩𝑶𝑻": st.session_state.messages_sr = []
        else: st.session_state.messages_falcon = []
        st.rerun()

# رمز SR
if st.session_state.bot_mode == "𝑺𝑹 𝑩𝑶𝑻" and not st.session_state.auth_sr:
    st.title("ورودی خصوصی")
    pwd = st.text_input("رمز عبور:", type="password")
    if st.button("تایید"):
        if pwd == "sara": st.session_state.auth_sr = True; st.rerun()
        else: st.error("رمز اشتباه")
    st.stop()

current_messages = st.session_state.messages_sr if st.session_state.bot_mode == "𝑺𝑹 𝑩𝑶𝑻" else st.session_state.messages_falcon

st.title(f"{st.session_state.bot_mode} {PERSONAS[st.session_state.persona]} {st.session_state.persona}")
mode = st.radio("", ["👁️ تحلیل عکس", "🎨 تولید تصویر", "💬 چت عادی"], index=2, horizontal=True)

model_key = None
uploaded_file = None
if mode == "👁️ تحلیل عکس":
    model_name = st.selectbox("مدل:", list(vision_model_options.keys()))
    model_key = vision_model_options[model_name]
    uploaded_file = st.file_uploader("آپلود عکس:", type=["jpg", "jpeg", "png"])

# نمایش پیام‌ها
for i, msg in enumerate(current_messages):
    with st.chat_message(msg["role"], avatar=PERSONAS[st.session_state.persona] if msg["role"] == "assistant" else None):
        if msg.get("type") == "image_gen": st.image(msg["content"])
        else: st.markdown(msg["content"])
        
        if msg["role"] == "assistant" and msg.get("type") != "image_gen":
            c1, c2, c3, c4 = st.columns([0.1, 0.1, 0.1, 0.7])
            with c1: 
                if st.button("📋", key=f"copy_{i}"): st.write(f"<script>navigator.clipboard.writeText(`{msg['content']}`)</script>", unsafe_allow_html=True); st.toast("کپی شد!")
            with c2: st.button("👍", key=f"like_{i}")
            with c3: st.button("👎", key=f"dislike_{i}")

if prompt := st.chat_input("𝑨𝑺𝑲 𝑭𝒂𝒍𝒄𝒐𝒏 𝑨𝑰"):
    current_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant", avatar=PERSONAS[st.session_state.persona]):
        if mode == "👁️ تحلیل عکس" and uploaded_file is not None:
            res = analyze_image(uploaded_file, prompt, model_key)
            st.markdown(res)
            current_messages.append({"role": "assistant", "content": res})
        elif mode == "🎨 تولید تصویر":
            tr_prompt = or_client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":f"Translate to English: {prompt}"}]).choices[0].message.content
            url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(tr_prompt)}?seed={random.randint(1,9999)}"
            st.image(url)
            current_messages.append({"role": "assistant", "content": url, "type": "image_gen"})
        else:
            res = (or_client if "/" in selected_model else groq_client).chat.completions.create(
                model=selected_model, 
                messages=[{"role":"system","content":PERSONA_PROMPTS[st.session_state.persona]}] + current_messages[-3:]
            ).choices[0].message.content
            st.markdown(res)
            current_messages.append({"role": "assistant", "content": res})
    fname = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(os.path.join(user_dir, fname), 'w', encoding='utf-8') as file: json.dump(current_messages, file)
    st.rerun()

```
