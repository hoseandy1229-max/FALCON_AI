import streamlit as st
from groq import Groq
from openai import OpenAI
import urllib.parse
import random 
import base64

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

groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"])

if "auth_sr" not in st.session_state: st.session_state.auth_sr = False
if "messages_falcon" not in st.session_state: st.session_state.messages_falcon = []
if "messages_sr" not in st.session_state: st.session_state.messages_sr = []

# --- سایدبار ---
with st.sidebar:
    bot_mode = st.radio("بخش:", ["FALCON AI", "SR BOT"])
    selected_model = st.selectbox("انتخاب مدل:", [
        "mistralai/pixtral-12b:free",
        "google/gemini-2.0-flash-lite-preview-02-05:free",
        "meta-llama/llama-3.2-11b-vision-instruct",
        "qwen/qwen-2.5-vl-72b-instruct:free"
    ])
    if st.button("Reset"):
        if bot_mode == "SR BOT": st.session_state.messages_sr = []
        else: st.session_state.messages_falcon = []
        st.rerun()

# لاگین SR BOT
if bot_mode == "SR BOT" and not st.session_state.auth_sr:
    if st.text_input("رمز:", type="password") == "1234":
        st.session_state.auth_sr = True
        st.session_state.messages_sr = [{"role": "assistant", "content": "سلام سارا جون."}]
        st.rerun()
    st.stop()

current_messages = st.session_state.messages_sr if bot_mode == "SR BOT" else st.session_state.messages_falcon
st.title("مخصوص سارا" if bot_mode == "SR BOT" else "𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰")

mode = st.radio("حالت:", ["💬 چت عادی", "🎨 تولید تصویر", "👁️ تحلیل عکس"], horizontal=True)

for msg in current_messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image_gen": st.image(msg["content"])
        else: st.markdown(msg["content"])

# --- تحلیل عکس ---
if mode == "👁️ تحلیل عکس":
    uploaded_file = st.file_uploader("عکس:", type=['jpg', 'png', 'jpeg'])
    image_prompt = st.text_input("سوال:")
    if uploaded_file and image_prompt:
        b64 = base64.b64encode(uploaded_file.read()).decode('utf-8')
        with st.chat_message("assistant"):
            res = or_client.chat.completions.create(model=selected_model, messages=[{"role":"user", "content":[{"type":"text", "text":image_prompt}, {"type":"image_url", "image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}])
            content = res.choices[0].message.content
            if bot_mode == "SR BOT": content += "\n\nچشم بانو."
            st.markdown(content)
            current_messages.append({"role": "assistant", "content": content})

# --- چت و تصویر ---
if prompt := st.chat_input("پیام..."):
    current_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant"):
        if mode == "🎨 تولید تصویر":
            url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&seed={random.randint(1,99999)}"
            st.image(url)
            current_messages.append({"role": "assistant", "content": url, "type": "image_gen"})
        else:
            sys = "تو دستیار سارایی. برای دستور کاری بگو چشم بانو." if bot_mode=="SR BOT" else "کوتاه پاسخ بده."
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system", "content":sys}]+current_messages).choices[0].message.content
            st.markdown(res)
            current_messages.append({"role": "assistant", "content": res})
    st.rerun()
