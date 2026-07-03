import streamlit as st
from groq import Groq
import random

# تنظیمات صفحه
st.set_page_config(page_title="Falcon AI", layout="wide")

# استایل سبز نئونی (حباب‌های چت و کادرها)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    [data-testid="stChatMessage"] { 
        border: 2px solid #39FF14 !important; 
        background-color: #1a1d23 !important;
        border-radius: 15px !important;
        padding: 10px !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# کلاینت گروک
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# مدیریت وضعیت‌ها
if "auth" not in st.session_state: st.session_state.auth = False
if "messages_falcon" not in st.session_state: st.session_state.messages_falcon = []
if "messages_sr" not in st.session_state: st.session_state.messages_sr = []

# --- سایدبار (منوی انتخاب بخش) ---
with st.sidebar:
    bot_mode = st.radio("بخش:", ["FALCON AI", "SR BOT"])
    
    # دکمه ریست
    if st.button("Reset"):
        if bot_mode == "SR BOT": st.session_state.messages_sr = []
        else: st.session_state.messages_falcon = []
        st.rerun()

# منطق ورود به SR BOT
if bot_mode == "SR BOT" and not st.session_state.auth:
    pwd = st.text_input("رمز ورود به بخش سارا:", type="password")
    if st.button("ورود"):
        if pwd == "1234":
            st.session_state.auth = True
            st.session_state.messages_sr = [{"role": "assistant", "content": "سلام سارا جون."}]
            st.rerun()
        else:
            st.error("رمز اشتباه است!")
    st.stop() # توقف برنامه تا زمانی که رمز درست وارد نشود

# تنظیمات نمایش بر اساس بخش انتخاب شده
current_messages = st.session_state.messages_sr if bot_mode == "SR BOT" else st.session_state.messages_falcon
page_title = "مخصوص سارا" if bot_mode == "SR BOT" else "𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰"

st.title(page_title)

# نمایش پیام‌های همان بخش
for msg in current_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- پردازش ورودی کاربر ---
if prompt := st.chat_input("پیام خود را بنویسید..."):
    # افزودن پیام کاربر به تاریخچه
    current_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # پردازش هوش مصنوعی
    with st.chat_message("assistant"):
        # دستورالعمل لحن برای سارا
        system_prompt = "تو یک دستیار هوشمند هستی. پاسخ کوتاه و فارسی بده."
        if bot_mode == "SR BOT":
            system_prompt = "تو دستیار سارا هستی. اگر کاربر دستور کاری داد (مثل انجام کار، نوشتن، حل مسئله، ادیت)، در انتها بگو: چشم بانو. اگر سوال معمولی بود، عادی پاسخ بده و چیزی اضافه نکن."
        
        try:
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system_prompt}] + current_messages
            )
            res = response.choices[0].message.content
            st.markdown(res)
            current_messages.append({"role": "assistant", "content": res})
        except Exception as e:
            st.error("خطا در ارتباط با سرور.")
