import streamlit as st
from groq import Groq

st.set_page_config(page_title="Falcon AI", layout="wide")

st.markdown("""
    <style>
    /* تنظیم کل صفحه */
    .stApp { background-color: #0e1117; color: white; }
    
    /* صورتی کردن کاملِ بخشِ سارا */
    .sara-bg { 
        background-color: #ffe4e6 !important; 
        padding: 20px; 
        border-radius: 20px;
    }
    
    /* آبی پاستیلی کردنِ حباب‌های چت */
    [data-testid="stChatMessage"] {
        background-color: #a7c7e7 !important;
        color: #000 !important;
    }
    
    /* صورتی کردنِ پس‌زمینه درونیِ چت‌بات */
    [data-testid="stChatInput"] {
        background-color: #ffe4e6 !important;
    }
    </style>
""", unsafe_allow_html=True)

api_key = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=api_key)

if st.sidebar.button("Reset"):
    st.session_state.clear()
    st.rerun()

mode = st.sidebar.radio("بخش:", ["📢 عمومی", "🌸 بخش سارا"])

def get_response(messages):
    system_instruction = {"role": "system", "content": "دستیار دقیق و حرفه‌ای. تعارف نکن."}
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[system_instruction] + messages
    )
    return response.choices[0].message.content

def render_chat(key):
    if key not in st.session_state: st.session_state[key] = []
    
    # نمایش پیام‌ها
    for msg in st.session_state[key]:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
            
    if prompt := st.chat_input("بنویس..."):
        st.session_state[key].append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            resp = get_response(st.session_state[key])
            st.markdown(resp)
            st.session_state[key].append({"role": "assistant", "content": resp})
            st.rerun()

if mode == "📢 عمومی":
    st.title("📢 فالکون عمومی")
    render_chat("messages")
else:
    # کانتینر برای صورتی کردن کلِ فضا
    st.markdown('<div class="sara-bg">', unsafe_allow_html=True)
    st.title("🌸 خلوتگاه سارا")
    if st.text_input("رمز:", type="password") == "1234":
        render_chat("sara_messages")
    else:
        st.warning("قفل است.")
    st.markdown('</div>', unsafe_allow_html=True)
