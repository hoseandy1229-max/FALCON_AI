import streamlit as st
from groq import Groq
from openai import OpenAI
import urllib.parse
import random 
import base64

# تنظیمات صفحه
st.set_page_config(page_title="Falcon AI", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    [data-testid="stChatMessage"] { border: 1px solid #39FF14 !important; }
    </style>
""", unsafe_allow_html=True)

# کلاینت‌ها
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"])

# مدیریت وضعیت
if "auth" not in st.session_state: st.session_state.auth = False

# --- سایدبار ---
with st.sidebar:
    if st.button("Reset"):
        st.session_state.messages = []
        st.rerun()
    
    st.write("بخش:")
    bot_mode = st.radio("", ["FALCON AI", "SR BOT"])
    
    st.write("---")
    model_choice = st.selectbox("انتخاب مدل:", [
        "mistralai/pixtral-12b:free", 
        "google/gemini-2.0-flash-lite-preview-02-05:free",
        "meta-llama/llama-3.2-11b-vision-instruct"
    ])

# مدیریتِ ورود به SR BOT
if bot_mode == "SR BOT" and not st.session_state.auth:
    pwd = st.text_input("رمز SR BOT:", type="password")
    if st.button("ورود"):
        if pwd == "1234": st.session_state.auth = True; st.rerun()
        else: st.error("رمز اشتباه است!")
    st.stop() # توقف برنامه تا زمانی که رمز درست وارد نشود

# --- منطقِ برنامه (بعد از تایید رمز) ---
st.title("𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰")

# اگر در بخش SR BOT هستیم، پیامِ خوش‌آمدگویی و لحنِ خاص
if bot_mode == "SR BOT":
    if len(st.session_state.messages) == 0:
        st.write("سلام بانو.")
        st.session_state.messages.append({"role": "assistant", "content": "سلام بانو."})

mode = st.radio("حالتِ کاری:", ["💬 چت عادی", "🎨 تولید تصویر", "👁️ تحلیل عکس"], horizontal=True)

if "messages" not in st.session_state: st.session_state.messages = []

# نمایش پیام‌ها
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image_gen": st.image(msg["content"])
        else: st.markdown(msg["content"])

# --- بخش تحلیل عکس ---
if mode == "👁️ تحلیل عکس":
    uploaded_file = st.file_uploader("عکس را آپلود کن:", type=['jpg', 'png', 'jpeg'])
    image_prompt = st.text_input("سوالت درباره این عکس چیه؟")
    if uploaded_file and image_prompt:
        bytes_data = uploaded_file.read()
        base64_img = base64.b64encode(bytes_data).decode('utf-8')
        with st.chat_message("assistant"):
            try:
                response = or_client.chat.completions.create(
                    model=model_choice,
                    messages=[{"role": "user", "content": [{"type": "text", "text": image_prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}]}],
                    max_tokens=500
                )
                res = response.choices[0].message.content.replace('assistant<|end_header_id|>', '')
                # اگر در حالتِ SR BOT هستیم، پایانِ هر پاسخ "چشم بانو" اضافه شود
                if bot_mode == "SR BOT": res += "\n\nچشم بانو."
                st.markdown(f"**پاسخ ({model_choice.split('/')[0]}):**\n\n{res}")
                st.session_state.messages.append({"role": "assistant", "content": res})
            except: st.error("خطا.")

# --- بخش چت و تولید تصویر ---
if prompt := st.chat_input("پیام یا دستور خود را بنویسید..."):
    if mode != "👁️ تحلیل عکس":
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        if mode == "🎨 تولید تصویر":
            url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(f'Real photo of {prompt}, 8k')}?width=1024&height=1024&seed={random.randint(1, 999999)}"
            st.image(url)
            st.session_state.messages.append({"role": "assistant", "content": url, "type": "image_gen"})
        elif mode == "💬 چت عادی":
            try:
                # اگر در حالت SR BOT هستیم، سیستم پرامپت را تغییر بده
                system_prompt = "کوتاه و فارسی پاسخ بده"
                if bot_mode == "SR BOT": system_prompt = "با لحنِ مطیع پاسخ بده و همیشه در انتها بگو چشم بانو."
                
                res = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages
                ).choices[0].message.content
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})
            except: st.error("خطا.")
    if mode != "👁️ تحلیل عکس": st.rerun()
