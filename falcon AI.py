import streamlit as st
from openai import OpenAI
from PIL import Image

# تنظیمات صفحه
st.set_page_config(page_title="Falcon AI", layout="wide")

# استایل‌های مشکی و پاستیلی
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .sara-box { background-color: #1e1e2e; padding: 25px; border-radius: 20px; border: 2px solid #ffb7c5; }
    </style>
""", unsafe_allow_html=True)

# کلاینت OpenAI
api_key = st.secrets.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# سایدبار
mode = st.sidebar.radio("انتخاب بخش:", ["📢 عمومی", "🌸 بخش سارا"])

def get_chatgpt_response(messages):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    return response.choices[0].message.content

def render_chat(messages_key, system_instruction):
    if messages_key not in st.session_state:
        st.session_state[messages_key] = [{"role": "system", "content": system_instruction}]
    
    # نمایش پیام‌ها
    for msg in st.session_state[messages_key]:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
            
    if prompt := st.chat_input("پیام خود را بنویسید..."):
        st.session_state[messages_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            response = get_chatgpt_response(st.session_state[messages_key])
            st.markdown(response)
            st.session_state[messages_key].append({"role": "assistant", "content": response})

# --- صفحات ---
if mode == "📢 عمومی":
    st.title("📢 فالکون عمومی")
    render_chat("messages", "تو یک دستیار هوشمند و وفادار به نام فالکون هستی. فارسی روان صحبت کن.")

else:
    st.title("🌸 خلوتگاه سارا")
    st.markdown('<div class="sara-box">', unsafe_allow_html=True)
    password = st.text_input("رمز ورود:", type="password")
    
    if password == "1234":
        render_chat("sara_messages", "تو دستیار اختصاصی سارا هستی. بسیار صمیمی و مهربان پاسخ بده.")
    else:
        st.warning("اینجا فقط برای ساراست...")
    st.markdown('</div>', unsafe_allow_html=True)
