import streamlit as st
from groq import Groq

# تنظیمات اصلی
st.set_page_config(page_title="Falcon AI", layout="wide")
api_key = st.secrets.get("GROQ_API_KEY")
client = Groq(api_key=api_key)

# سایدبار
mode = st.sidebar.radio("انتخاب بخش:", ["📢 عمومی", "🌸 بخش سارا"])

def get_response(prompt, messages_key):
    # این تابع فقط متن خالص را برمی‌گرداند تا قاطی نشود
    chat_completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=st.session_state[messages_key]
    )
    return chat_completion.choices[0].message.content

# --- منطق نمایش چت ---
def render_chat(messages_key):
    if messages_key not in st.session_state:
        st.session_state[messages_key] = []
    
    # نمایش پیام‌های قبلی به صورت پنل‌های جدا
    for msg in st.session_state[messages_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # دریافت پیام جدید
    if prompt := st.chat_input("پیام خود را بنویسید..."):
        st.session_state[messages_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            response = get_response(prompt, messages_key)
            st.markdown(response)
            st.session_state[messages_key].append({"role": "assistant", "content": response})

# --- صفحات ---
if mode == "📢 عمومی":
    st.title("📢 فالکون عمومی")
    render_chat("messages")

else:
    st.title("🌸 خلوتگاه سارا")
    password = st.text_input("رمز ورود:", type="password")
    if password == "1234":
        render_chat("sara_messages")
    else:
        st.warning("رمز را وارد کن...")
