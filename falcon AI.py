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

mode = st.sidebar.radio("بخش:", ["📢 عمومی", "🌸 بخش سارا"])

def get_response(messages):
    # اینجاست که جلویِ هذیانِ مدل را می‌گیریم
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "system", "content": "تو دستیارِ صمیمی هستی. فقط به پیام کاربر پاسخ بده و خودت شروع‌کننده نباش."}] + messages
    )
    return response.choices[0].message.content

def render_chat(key):
    if key not in st.session_state: st.session_state[key] = []
    
    # نمایش تاریخچه
    for msg in st.session_state[key]:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
            
    # فقط اگر ورودیِ جدیدی از کاربر بیاید، ربات اجرا می‌شود
    if prompt := st.chat_input("بنویس..."):
        st.session_state[key].append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            resp = get_response(st.session_state[key])
            st.markdown(resp)
            st.session_state[key].append({"role": "assistant", "content": resp})
            # اضافه کردن این دستور برای رفرش شدن صفحه پس از پاسخ
            st.rerun()

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
