import streamlit as st
from groq import Groq
import urllib.parse

st.set_page_config(page_title="Falcon AI", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    [data-testid="stChatMessage"] { background-color: #000000 !important; border: 1px solid #39FF14 !important; }
    [data-testid="stChatMessage"] p { color: #39FF14 !important; }
    </style>
""", unsafe_allow_html=True)

api_key = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=api_key)

def get_sara_response(messages):
    # دستورالعمل بسیار سخت‌گیرانه برای جلوگیری از هذیان
    system_instruction = {
        "role": "system", 
        "content": "تو دستیار شخصی سارا هستی. فقط و فقط با عبارت 'چشم بانو' پاسخ را شروع کن. هرگز پاسخ‌های طولانی یا فلسفی نده. اگر سوالی در مورد احوالپرسی یا کار شخصی است، فقط پاسخ مستقیم بده و از اضافه گویی بپرهیز."
    }
    response = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[system_instruction] + messages)
    return response.choices[0].message.content

def render_sara_chat(key):
    if key not in st.session_state: st.session_state[key] = []
    for msg in st.session_state[key]:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
            
    if prompt := st.chat_input("𝑨𝒔𝒌 𝑴𝒚 𝑸𝒖𝒆𝒆𝒏"):
        st.session_state[key].append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            resp = get_sara_response(st.session_state[key])
            st.markdown(resp)
            st.session_state[key].append({"role": "assistant", "content": resp})
            st.rerun()

# لاجیک ورود مخفیانه
if 'auth' not in st.session_state: st.session_state['auth'] = False

mode = st.sidebar.radio("بخش:", ["𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰", "𝑺𝑹 𝑩𝑶𝑻"])

if mode == "𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰":
    st.title("𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰")
    # ... (کد چت معمولی فالکون)
else:
    if not st.session_state['auth']:
        # صفحه کاملاً خالی قبل از ورود
        password = st.text_input("ورود:", type="password")
        if st.button("تایید ورود"):
            if password == "sara":
                st.session_state['auth'] = True
                st.rerun()
            else:
                st.error("رمز اشتباه است.")
    else:
        # بعد از ورود فقط یک صفحه چت ظاهر می‌شود
        st.title("بخش اختصاصی")
        render_sara_chat("sara_messages")
        if st.button("خروج"): st.session_state['auth'] = False; st.rerun()
