import streamlit as st
from groq import Groq
from openai import OpenAI
import random 
import json
import os

# تنظیمات اصلی
st.set_page_config(page_title="Falcon AI", layout="wide")
if not os.path.exists("history"): os.makedirs("history")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    [data-testid="stChatMessage"] { border: 2px solid #39FF14 !important; background-color: #1a1d23 !important; border-radius: 15px !important; padding: 10px !important; }
    </style>
""", unsafe_allow_html=True)

# تنظیمات کلاینت‌ها
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"])
chat_models = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "meta-llama/llama-3.1-405b", "qwen/qwen-2.5-72b-instruct"]

# سیستم احراز هویت و ارتقا به ادمین
if "username" not in st.session_state:
    st.session_state.username = "a"

# مدیریت پوشه کاربر
user_dir = f"history/{st.session_state.username}"
if not os.path.exists(user_dir): os.makedirs(user_dir)
if "messages_sr" not in st.session_state: st.session_state.messages_sr = []

# سایدبار
with st.sidebar:
    st.write(f"کاربر: {st.session_state.username}")
    
    # بخش رمز عبور برای ادمین
    with st.expander("🔐 تغییر وضعیت به ادمین"):
        password = st.text_input("رمز عبور:", type="password")
        if st.button("تایید"):
            if password == "1234": # رمز عبور خود را اینجا تغییر دهید
                st.session_state.username = "admin"
                st.rerun()
            else:
                st.error("رمز اشتباه است!")

    bot_mode = st.radio("بخش:", ["FALCON AI", "SR BOT"])
    selected_model = st.selectbox("مدل:", chat_models)
    
    st.subheader("سوابق من")
    user_files = [f for f in os.listdir(user_dir) if f.endswith(".json")]
    for file in user_files:
        if st.button(file):
            with open(os.path.join(user_dir, file), 'r') as f:
                st.session_state.messages_sr = json.load(f)
                st.rerun()
    
    if st.button("شروع گفتگو جدید"):
        chat_name = f"chat_{random.randint(100, 999)}.json"
        with open(os.path.join(user_dir, chat_name), 'w') as f: json.dump(st.session_state.messages_sr, f)
        st.session_state.messages_sr = []
        st.rerun()

    # پنل ادمین
    if st.session_state.username == "admin":
        st.divider()
        st.subheader("⚠️ پنل ادمین")
        all_users = [d for d in os.listdir("history/") if os.path.isdir(os.path.join("history/", d))]
        if all_users:
            sel_user = st.selectbox("انتخاب کاربر:", all_users)
            user_chats = [f for f in os.listdir(f"history/{sel_user}") if f.endswith(".json")]
            if user_chats:
                sel_chat = st.selectbox("انتخاب چت:", user_chats)
                if st.button("مشاهده چت"):
                    with open(f"history/{sel_user}/{sel_chat}", 'r') as f:
                        st.json(json.load(f))
            else: st.info("کاربر چتی ندارد.")

# نمایش چت
st.title("𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰")

for msg in st.session_state.messages_sr:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("پیام..."):
    st.session_state.messages_sr.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant"):
        recent_messages = [{"role":"system","content":"تو دستیار هستی."}] + st.session_state.messages_sr[-5:]
        res = or_client.chat.completions.create(
            model=selected_model, messages=recent_messages, temperature=0.2
        ).choices[0].message.content
        st.markdown(res)
        st.session_state.messages_sr.append({"role": "assistant", "content": res})
    st.rerun()
