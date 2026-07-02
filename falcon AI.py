import streamlit as st
from groq import Groq

st.set_page_config(page_title="Falcon AI", layout="wide")

# استایل برای تغییر رنگِ کل صفحه در بخشِ سارا
st.markdown("""
    <style>
    /* استایل عمومی */
    .stApp { background-color: #0e1117; color: white; }
    
    /* استایل اختصاصی برای صورتی کردنِ کل صفحه در بخشِ سارا */
    .sara-page { 
        background-color: #ffe4e6 !important; 
        min-height: 100vh;
        padding: 20px;
        color: #333;
    }
    
    /* آبی پاستیلی کردنِ حباب‌های چت */
    div[data-testid="stChatMessage"] {
        background-color: #a7c7e7 !important;
        color: #000 !important;
    }
    </style>
""", unsafe_allow_html=True)

api_key = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=api_key)

if st.sidebar.button("پاکسازی حافظه (Reset)"):
    st.session_state.clear()
    st.rerun()

mode = st.sidebar.radio("بخش:", ["📢 عمومی", "🌸 بخش سارا"])

def get_response(messages):
    system_instruction = {"role": "system", "content": "تو دستیار هوشمند فالکون هستی. مستقیم و دقیق پاسخ بده. از تعارفات پرهیز کن."}
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[system_instruction] + messages
    )
    return response.choices[0].message.content

def render_chat(key):
    if key not in st.session_state: st.session_state[key] = []
    for msg in st.session_state[key]:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
            
    if prompt := st.chat_input("سوالی بپرس..."):
        st.session_state[key].append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            resp = get_response(st.session_state[key])
            st.markdown(resp)
            st.session_state[key].append({"role": "assistant", "content": resp})
            st.rerun()

# منطق صفحات
if mode == "📢 عمومی":
    st.title("📢 فالکون عمومی")
    render_chat("messages")
else:
    # اینجا کل محتوا داخل یک دیوِ صورتی قرار می‌گیرد
    st.markdown('<div class="sara-page">', unsafe_allow_html=True)
    st.title("🌸 خلوتگاه سارا")
    password = st.text_input("رمز عبور:", type="password")
    if password == "1234":
        render_chat("sara_messages")
    else:
        st.warning("دسترسی محدود است.")
    st.markdown('</div>', unsafe_allow_html=True)
