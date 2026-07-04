import streamlit as st
from groq import Groq
from openai import OpenAI
import urllib.parse, random, base64, json, os, shutil
from datetime import datetime
from streamlit_cookies_manager import EncryptedCookieManager
# کتابخانه‌های جدید
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# مدیریت کوکی و تنظیمات
cookies = EncryptedCookieManager(prefix="falcon_ai", password="some_secret_password")
if not cookies.ready(): st.stop()
if not os.path.exists("history"): os.makedirs("history")
st.set_page_config(page_title="Falcon AI Pro", layout="wide")

# استایل‌ها
st.markdown("""<style>.stApp { background-color: #0e1117; color: white; } [data-testid="stChatMessage"] { border: 2px solid #39FF14 !important; background-color: #1a1d23 !important; border-radius: 15px !important; }</style>""", unsafe_allow_html=True)

# سیستم‌ها
PERSONAS = {"دستیار": "تو یک دستیار هوشمند هستی.", "دانا": "تو یک دانشمند هستی.", "سارا": "تو یک دوست صمیمی هستی."}
vision_models = {"Gemini Flash": "google/gemini-2.5-flash", "Llama 3.2": "meta-llama/llama-3.2-11b-vision-instruct"}

# کلاینت‌ها
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"])
search_tool = TavilySearchResults(api_key=st.secrets["TAVILY_API_KEY"])
embeddings = OpenAIEmbeddings(openai_api_key=st.secrets["OPENAI_API_KEY"])

# لاگین
if "username" not in st.session_state:
    if "username" in cookies: st.session_state.username = cookies["username"]
    else:
        st.title("ورود"); user_input = st.text_input("نام کاربری:"); 
        if st.button("تایید"): st.session_state.username = user_input; cookies["username"] = user_input; cookies.save(); st.rerun()
        st.stop()

# وضعیت و حافظه
user_dir = f"history/{st.session_state.username}"
if not os.path.exists(user_dir): os.makedirs(user_dir)
vector_db = Chroma(persist_directory=f"{user_dir}/chroma_db", embedding_function=embeddings)

if "messages_falcon" not in st.session_state: st.session_state.messages_falcon = []
if "messages_sr" not in st.session_state: st.session_state.messages_sr = []
if "bot_mode" not in st.session_state: st.session_state.bot_mode = "FALCON AI"

# سایدبار
with st.sidebar:
    st.write(f"کاربر: {st.session_state.username}")
    st.session_state.bot_mode = st.radio("بخش:", ["FALCON AI", "SR BOT"])
    st.session_state.persona = st.selectbox("شخصیت:", list(PERSONAS.keys()))
    if st.expander("🔐 پنل ادمین"):
        if st.text_input("رمز:", type="password") == "admin123" and st.button("پاکسازی کل"): shutil.rmtree("history"); st.rerun()

current_messages = st.session_state.messages_sr if st.session_state.bot_mode == "SR BOT" else st.session_state.messages_falcon

# منطق اصلی پاسخ‌دهی
st.title(f"{st.session_state.bot_mode}")
mode = st.radio("", ["👁️ تحلیل عکس", "🎨 تولید تصویر", "💬 چت عادی"], index=2, horizontal=True)

for msg in current_messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("پیام..."):
    current_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        # 1. تحلیل عکس
        if mode == "👁️ تحلیل عکس":
            res = "تحلیل عکس انجام شد." # منطق قبلی شما
        # 2. تولید تصویر (با ترجمه)
        elif mode == "🎨 تولید تصویر":
            prompt_en = or_client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":f"Translate to English: {prompt}"}]).choices[0].message.content
            res = f"https://pollinations.ai/p/{urllib.parse.quote(prompt_en)}"
            st.image(res)
        # 3. وب‌گردی و چت عادی
        else:
            mem = vector_db.similarity_search(prompt, k=1)
            web = search_tool.invoke(prompt) if "خبر" in prompt else ""
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":f"Mem: {mem}, Web: {web}, Q: {prompt}"}]).choices[0].message.content
            st.markdown(res)
            vector_db.add_texts([f"U: {prompt}, A: {res}"])
    
    current_messages.append({"role": "assistant", "content": res})
    with open(f"{user_dir}/chat_{datetime.now().strftime('%Y%m%d%H%M%S')}.json", 'w', encoding='utf-8') as f: json.dump(current_messages, f)
    st.rerun()
