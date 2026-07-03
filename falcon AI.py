import streamlit as st
from groq import Groq
from openai import OpenAI
import urllib.parse
import random 
import base64
import json
import os

# ایجاد پوشه تاریخچه
if not os.path.exists("history"): os.makedirs("history")

st.set_page_config(page_title="Falcon AI", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    [data-testid="stChatMessage"] { 
        border: 2px solid #39FF14 !important; 
        background-color: #1a1d23 !important;
        border-radius: 15px !important;
        padding: 10px !important;
    }
    </style>
""", unsafe_allow_html=True)

# مدیریت ورود نام کاربری
if "username" not in st.session_state:
    st.title("ورود به Falcon AI")
    user_input = st.text_input("نام کاربری خود را وارد کنید:")
    if st.button("تایید و ورود"):
        st.session_state.username = user_input
        st.rerun()
    st.stop()

# تنظیمات کلاینت‌ها
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"])

if "messages_falcon" not in st.session_state: st.session_state.messages_falcon = []
if "messages_sr" not in st.session_state: st.session_state.messages_sr = []
if "auth_sr" not in st.session_state: st.session_state.auth_sr = False

chat_models = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "meta-llama/llama-3.1-405b", "qwen/qwen-2.5-72b-instruct"]

# مسیر فایل کاربر
user_dir = f"history/{st.session_state.username}"
if not os.path.exists(user_dir): os.makedirs(user_dir)

with st.sidebar:
    st.write(f"کاربر: {st.session_state.username}")
    bot_mode = st.radio("بخش:", ["FALCON AI", "SR BOT"])
    selected_model = st.selectbox("انتخاب مدل:", chat_models)
    
    # بخش تاریخچه
    st.subheader("تاریخچه گفتگوها")
    files = [f for f in os.listdir(user_dir) if f.endswith(".json")]
    for f in files:
        if st.button(f):
            with open(os.path.join(user_dir, f), 'r') as file:
                st.session_state.messages_sr = json.load(file)
                st.rerun()
    
    if st.button("ذخیره و شروع جدید"):
        fname = f"chat_{random.randint(1000,9999)}.json"
        with open(os.path.join(user_dir, fname), 'w') as file: json.dump(st.session_state.messages_sr, file)
        st.session_state.messages_sr = []
        st.rerun()

    # بخش ادمین ایمن‌سازی شده
    with st.expander("🔐 پنل ادمین"):
        admin_pwd = st.text_input("رمز ادمین:", type="password")
        if admin_pwd == "admin123":
            all_users = os.listdir("history/")
            sel_u = st.selectbox("کاربر:", all_users)
            if sel_u:
                user_files = os.listdir(f"history/{sel_u}")
                sel_f = st.selectbox("چت:", user_files)
                if sel_f and st.button("مشاهده"):
                    file_path = f"history/{sel_u}/{sel_f}"
                    if os.path.exists(file_path):
                        with open(file_path, 'r') as file:
                            chat_data = json.load(file)
                            for msg in chat_data:
                                role = "👤 کاربر" if msg.get("role") == "user" else "🤖 دستیار"
                                st.write(f"**{role}:** {msg.get('content', '')}")
                    else:
                        st.error("فایل پیدا نشد!")
        elif admin_pwd: st.error("رمز غلط")

if bot_mode == "SR BOT" and not st.session_state.auth_sr:
    pwd = st.text_input("رمز سارا:", type="password")
    if st.button("تایید ورود"):
        if pwd == "sara":
            st.session_state.auth_sr = True
            st.rerun()
        else: st.error("رمز اشتباه است!")
    st.stop()

current_messages = st.session_state.messages_sr if bot_mode == "SR BOT" else st.session_state.messages_falcon
st.title("مخصوص سارا" if bot_mode == "SR BOT" else "𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰")
mode = st.radio("حالت:", ["💬 چت عادی", "🎨 تولید تصویر", "👁️ تحلیل عکس"], horizontal=True)

for msg in current_messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image_gen": st.image(msg["content"])
        else: st.markdown(msg["content"])

if mode == "👁️ تحلیل عکس":
    uploaded_file = st.file_uploader("عکس:", type=['jpg', 'png', 'jpeg'])
    img_prompt = st.text_input("سوال:", value="توضیح بده.")
    
    if uploaded_file and st.button("تحلیل"):
        with st.spinner("در حال پردازش..."):
            b64 = base64.b64encode(uploaded_file.read()).decode('utf-8')
            vision_models = ["google/gemini-2.0-flash-exp", "meta-llama/llama-3.2-11b-vision-instruct"]
            for model_id in vision_models:
                try:
                    res = or_client.chat.completions.create(model=model_id, messages=[{"role": "user", "content": [{"type": "text", "text": img_prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}], temperature=0.2)
                    content = res.choices[0].message.content
                    st.markdown(f"**پاسخ:**\n{content}")
                    current_messages.append({"role": "assistant", "content": content})
                    break 
                except: continue

elif prompt := st.chat_input("پیام..."):
    current_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant"):
        if mode == "🎨 تولید تصویر":
            trans = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":"Translate to detailed English prompt."},{"role":"user","content":prompt}]).choices[0].message.content
            url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(trans)}?width=1024&height=1024&seed={random.randint(1,99999)}"
            st.image(url)
            current_messages.append({"role": "assistant", "content": url, "type": "image_gen"})
        else:
            sys_content = "تو دستیار سارا هستی. پاسخ‌ها باید کاملاً فارسی، دقیق و منطقی باشند."
            recent_messages = [{"role":"system","content":sys_content}] + current_messages[-5:]
            client = or_client if "/" in selected_model else groq_client
            res = client.chat.completions.create(model=selected_model, messages=recent_messages, temperature=0.2, frequency_penalty=0.8, stop=["\n\n", "###", "</s>"]).choices[0].message.content
            st.markdown(res)
            current_messages.append({"role": "assistant", "content": res})
    st.rerun()
