import streamlit as st
from groq import Groq
from openai import OpenAI
import base64

# تنظیمات صفحه
st.set_page_config(page_title="Falcon AI", layout="wide")

# استایل‌دهی
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    [data-testid="stChatMessage"] { border: 2px solid #39FF14 !important; background-color: #1a1d23 !important; border-radius: 15px !important; padding: 10px !important; }
    </style>
""", unsafe_allow_html=True)

# کلاینت‌ها
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"])

# مدیریت وضعیت
if "auth_sr" not in st.session_state: st.session_state.auth_sr = False

with st.sidebar:
    bot_mode = st.radio("بخش:", ["FALCON AI", "SR BOT"])
    if st.button("Reset"): st.rerun()

# لاگین اختصاصی برای سارا
if bot_mode == "SR BOT" and not st.session_state.auth_sr:
    pwd = st.text_input("رمز سارا:", type="password")
    if st.button("تایید ورود"):
        if pwd == "sara":
            st.session_state.auth_sr = True
            st.rerun()
        else:
            st.error("رمز اشتباه است!")
    st.stop()

st.title("مخصوص سارا" if bot_mode == "SR BOT" else "𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰")
mode = st.radio("حالت:", ["💬 چت عادی", "👁️ تحلیل عکس"], horizontal=True)

# بخش تحلیل عکس
if mode == "👁️ تحلیل عکس":
    uploaded_file = st.file_uploader("عکس:", type=['jpg', 'jpeg', 'png'])
    img_prompt = st.text_input("سوال:", value="خوبه؟")
    
    if uploaded_file and st.button("تحلیل"):
        with st.spinner("در حال اتصال و تحلیل..."):
            try:
                b64 = base64.b64encode(uploaded_file.read()).decode('utf-8')
                res = or_client.chat.completions.create(
                    model="google/gemini-2.0-flash-lite-preview-02-05:free",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": img_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                        ]
                    }]
                )
                st.markdown(f"**پاسخ:** {res.choices[0].message.content}")
            except Exception as e:
                st.error("خطا در ارتباط با سرور. لطفاً دوباره تلاش کن.")
                st.write(f"جزئیات فنی: {e}")

# بخش چت عادی
else:
    if prompt := st.chat_input("پیام..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            try:
                res = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}]
                )
                answer = res.choices[0].message.content
                if bot_mode == "SR BOT": answer += "\n\nچشم بانو."
                st.markdown(answer)
            except Exception as e:
                st.error("خطا در پاسخ‌دهی!")
