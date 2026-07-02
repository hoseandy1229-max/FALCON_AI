import streamlit as st
from groq import Groq

# تنظیمات ظاهری
st.set_page_config(page_title="Falcon AI", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .sara-box { background-color: #1e1e2e; padding: 25px; border-radius: 20px; border: 2px solid #ffb7c5; }
    </style>
""", unsafe_allow_html=True)

# تنظیمات Groq
api_key = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=api_key)

# دکمه ریست حافظه
if st.sidebar.button("پاکسازی حافظه (Reset)"):
    st.session_state.clear()
    st.rerun()

mode = st.sidebar.radio("بخش:", ["📢 عمومی", "🌸 بخش سارا"])

def get_response(messages):
    # دستور جدی و مستقیم - بدون تعارف
    system_instruction = {
        "role": "system", 
        "content": "تو دستیار هوشمند فالکون هستی. مستقیم، دقیق و حرفه‌ای پاسخ بده. از تعارفاتِ بی‌مورد مثل 'خوش آمدید' یا 'خوب باش' کاملاً پرهیز کن."
    }
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
            
    # دریافت پیام
    if prompt := st.chat_input("سوالی بپرس..."):
        st.session_state[key].append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            resp = get_response(st.session_state[key])
            st.markdown(resp)
            st.session_state[key].append({"role": "assistant", "content": resp})
            st.rerun()

# صفحات
if mode == "📢 عمومی":
    st.title("📢 فالکون عمومی")
    render_chat("messages")
else:
    st.title("🌸 خلوتگاه سارا")
    st.markdown('<div class="sara-box">', unsafe_allow_html=True)
    if st.text_input("رمز عبور:", type="password") == "1234":
        render_chat("sara_messages")
    else:
        st.warning("دسترسی محدود است.")
    st.markdown('</div>', unsafe_allow_html=True)
