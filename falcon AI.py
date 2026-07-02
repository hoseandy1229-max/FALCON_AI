import streamlit as st
from groq import Groq

st.set_page_config(page_title="Falcon AI", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .sara-box { background-color: #1e1e2e; padding: 25px; border-radius: 20px; border: 2px solid #ffb7c5; }
    </style>
""", unsafe_allow_html=True)

api_key = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=api_key)

# دکمه برای پاکسازی کامل حافظه ربات
if st.sidebar.button("Reset Chat"):
    st.session_state.clear()
    st.rerun()

mode = st.sidebar.radio("بخش:", ["📢 عمومی", "🌸 بخش سارا"])

def get_response(messages):
    # سیستم پرامپت بسیار خنثی
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "system", "content": "فقط به پیام کاربر پاسخ بده. هیچ سوالی نپرس و هیچ چیزی اضافه نکن."}] + messages
    )
    return response.choices[0].message.content

def render_chat(key):
    if key not in st.session_state: st.session_state[key] = []
    
    # نمایش پیام‌ها
    for msg in st.session_state[key]:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
            
    # دریافت ورودی جدید
    if prompt := st.chat_input("بنویس..."):
        # اضافه کردن پیام کاربر
        st.session_state[key].append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        # تولید پاسخ
        with st.chat_message("assistant"):
            resp = get_response(st.session_state[key])
            st.markdown(resp)
            st.session_state[key].append({"role": "assistant", "content": resp})

if mode == "📢 عمومی":
    st.title("📢 فالکون عمومی")
    render_chat("messages")
else:
    st.title("🌸 خلوتگاه سارا")
    st.markdown('<div class="sara-box">', unsafe_allow_html=True)
    if st.text_input("رمز:", type="password") == "1234":
        render_chat("sara_messages")
    else:
        st.warning("رمز اشتباه است.")
    st.markdown('</div>', unsafe_allow_html=True)
