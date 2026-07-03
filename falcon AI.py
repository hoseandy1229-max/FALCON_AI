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

if "messages_falcon" not in st.session_state: st.session_state.messages_falcon = []
if "messages_sr" not in st.session_state: st.session_state.messages_sr = []
if "auth_sr" not in st.session_state: st.session_state.auth_sr = False

chat_models = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "meta-llama/llama-3.1-405b", "qwen/qwen-2.5-72b-instruct"]

with st.sidebar:
    bot_mode = st.radio("بخش:", ["FALCON AI", "SR BOT"])
    selected_model = st.selectbox("انتخاب مدل:", chat_models)
    if st.button("Reset"):
        if bot_mode == "SR BOT": st.session_state.messages_sr = []
        else: st.session_state.messages_falcon = []
        st.rerun()

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
        with st.spinner("در حال اتصال به سرور..."):
            b64 = base64.b64encode(uploaded_file.read()).decode('utf-8')
            vision_models = ["google/gemini-2.0-flash-exp", "meta-llama/llama-3.2-11b-vision-instruct"]
            success = False
            
            for model_id in vision_models:
                try:
                    res = or_client.chat.completions.create(
                        model=model_id,
                        messages=[{"role": "user", "content": [{"type": "text", "text": img_prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}],
                        temperature=0.3
                    )
                    content = res.choices[0].message.content
                    st.markdown(f"**پاسخ ({model_id.split('/')[0]}):**\n{content}")
                    current_messages.append({"role": "assistant", "content": content})
                    success = True
                    break 
                except:
                    continue 
            
            if not success:
                st.error("ارتباط با تمام مدل‌های تحلیل برقرار نشد.")

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
            sys_content = "تو دستیار سارا هستی. پاسخ‌هایت باید دقیق، منطقی، کوتاه و کاملاً مرتبط با متن سارا باشد. از تکرار، خیال‌پردازی و حرف‌های اضافه جداً خودداری کن." if bot_mode=="SR BOT" else "پاسخ‌ها باید مستقیم، کوتاه و دقیق باشند."
            client = or_client if "/" in selected_model else groq_client
            
            res = client.chat.completions.create(
                model=selected_model, 
                messages=[{"role":"system","content":sys_content}]+current_messages,
                temperature=0.3
            ).choices[0].message.content
            
            st.markdown(res)
            current_messages.append({"role": "assistant", "content": res})
    st.rerun()
