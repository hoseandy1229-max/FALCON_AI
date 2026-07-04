import streamlit as st
from groq import Groq
from openai import OpenAI
import urllib.parse, random, base64, json, os
from datetime import datetime
from streamlit_cookies_manager import EncryptedCookieManager
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# مدیریت کوکی
cookies = EncryptedCookieManager(prefix="falcon_ai", password="some_secret_password")
if not cookies.ready(): st.stop()

if not os.path.exists("history"): os.makedirs("history")
st.set_page_config(page_title="Falcon AI", layout="wide")

# استایل‌ها
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    [data-testid="stChatMessage"] { border: 2px solid #39FF14 !important; background-color: #1a1d23 !important; border-radius: 15px !important; }
    </style>
""", unsafe_allow_html=True)

# سیستم شخصیت‌ها
PERSONAS = {
    "دستیار (منظم)": "تو یک دستیار هوشمند و بسیار منظم هستی.",
    "دانا (دانشمند)": "تو یک دانشمند هستی که با دقت و علمی پاسخ می‌دهی.",
    "سارا (دوست‌داشتنی)": "تو یک دوست صمیمی هستی.",
    "استاد (سخت‌گیر)": "تو یک استاد سخت‌گیر هستی.",
    "شوخ (طناز)": "تو همیشه با شوخی پاسخ می‌دهی.",
    "فیلسوف (متفکر)": "تو با دیدگاه عمیق نگاه می‌کنی.",
    "نویسنده (خلاق)": "تو با ادبیاتی شاعرانه پاسخ می‌دهی.",
    "کدنویس (منطقی)": "تو تمرکزت روی منطق است.",
    "مربی (انگیزشی)": "تو پر از انرژی هستی."
}

# کلاینت‌ها و ابزارها
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"])
search_tool = TavilySearchResults(api_key=st.secrets["TAVILY_API_KEY"])
embeddings = OpenAIEmbeddings(openai_api_key=st.secrets["OPENAI_API_KEY"])

# لاگین
if "username" not in st.session_state:
    if "username" in cookies: st.session_state.username = cookies["username"]
    else:
        st.title("ورود به Falcon AI"); user_input = st.text_input("نام کاربری:"); 
        if st.button("تایید"): st.session_state.username = user_input; cookies["username"] = user_input; cookies.save(); st.rerun()
        st.stop()

# تنظیمات وضعیت
user_dir = f"history/{st.session_state.username}"
if not os.path.exists(user_dir): os.makedirs(user_dir)
vector_db = Chroma(persist_directory=f"{user_dir}/chroma_db", embedding_function=embeddings)

if "messages_falcon" not in st.session_state: st.session_state.messages_falcon = []
if "messages_sr" not in st.session_state: st.session_state.messages_sr = []
if "auth_sr" not in st.session_state: st.session_state.auth_sr = False
if "bot_mode" not in st.session_state: st.session_state.bot_mode = "FALCON AI"

# سایدبار
with st.sidebar:
    st.write(f"کاربر: {st.session_state.username}")
    new_mode = st.radio("بخش:", ["FALCON AI", "SR BOT"], index=0 if st.session_state.bot_mode=="FALCON AI" else 1)
    if new_mode != st.session_state.bot_mode: st.session_state.bot_mode = new_mode; st.session_state.auth_sr = False; st.rerun()
    st.session_state.persona = st.selectbox("شخصیت:", list(PERSONAS.keys()))

# رمز سارا
if st.session_state.bot_mode == "SR BOT" and not st.session_state.auth_sr:
    if st.text_input("رمز سارا:", type="password") == "sara": st.session_state.auth_sr = True; st.rerun()
    st.stop()

current_messages = st.session_state.messages_sr if st.session_state.bot_mode == "SR BOT" else st.session_state.messages_falcon

st.title(f"{st.session_state.bot_mode} - {st.session_state.persona}")
mode = st.radio("", ["👁️ تحلیل عکس", "🎨 تولید تصویر", "💬 چت عادی"], index=2, horizontal=True)

# نمایش چت
for msg in current_messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image_gen": st.image(msg["content"])
        else: st.markdown(msg["content"])

# لاجیک پاسخ‌دهی
if prompt := st.chat_input("پیام..."):
    current_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.status("در حال پردازش هوشمند...", expanded=True) as status:
            # 1. بازیابی حافظه بلندمدت
            memory_context = vector_db.similarity_search(prompt, k=2)
            # 2. جستجوی وب (در صورت نیاز)
            web_info = search_tool.invoke(prompt) if any(word in prompt for word in ["قیمت", "اخبار", "جدید"]) else ""
            
            combined_prompt = f"حافظه قبلی: {memory_context}. اطلاعات وب: {web_info}. سوال: {prompt}"
            
            res = (or_client if "/" in "llama-3.3-70b-versatile" else groq_client).chat.completions.create(
                model="llama-3.3-70b-versatile", messages=[{"role":"system","content":PERSONAS[st.session_state.persona]}] + [{"role":"user", "content": combined_prompt}]
            ).choices[0].message.content
            
            st.markdown(res)
            # 3. ذخیره در حافظه برای آینده
            vector_db.add_texts([f"User: {prompt}, AI: {res}"])
            status.update(label="پاسخ آماده شد!", state="complete", expanded=False)
    
    current_messages.append({"role": "assistant", "content": res})
    with open(f"{user_dir}/chat_{datetime.now().strftime('%Y%m%d%H%M%S')}.json", 'w', encoding='utf-8') as f: json.dump(current_messages, f)
    st.rerun()
