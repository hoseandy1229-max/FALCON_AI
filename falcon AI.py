import streamlit as st
from groq import Groq
import urllib.parse

st.set_page_config(page_title="Falcon AI", layout="wide")

# استایل حباب‌ها
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    [data-testid="stChatMessage"] { background-color: #000000 !important; border: 1px solid #39FF14 !important; }
    [data-testid="stChatMessage"] p { color: #39FF14 !important; }
    </style>
""", unsafe_allow_html=True)

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# تنظیمات سایدبار (مدل و ابزار)
st.sidebar.title("تنظیمات")
selected_model = st.sidebar.selectbox("انتخاب مدل:", ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"])
tool_mode = st.sidebar.checkbox("حالت تولید تصویر")
mode = st.sidebar.radio("بخش:", ["𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰", "𝑺𝑹 𝑩𝑶𝑻"])

def get_response(messages, is_sara=False):
    if is_sara:
        sys = {"role": "system", "content": "تو دستیار شخصی سارا هستی. قوانین: ۱. پاسخ را فقط با 'چشم بانو' شروع کن. ۲. فقط فارسی بنویس. ۳. هیچ کاراکتر غیرفارسی استفاده نکن. ۴. مطلقاً هذیان نگو و پاسخ‌ها را بسیار کوتاه و دقیق بده."}
        # برای سارا همیشه از بهترین مدل استفاده می‌کنیم تا هذیان نگوید
        model_to_use = "llama-3.3-70b-versatile"
        temp = 0.2
    else:
        sys = {"role": "system", "content": "دستیار حرفه‌ای و دقیق."}
        model_to_use = selected_model
        temp = 0.7
    
    response = client.chat.completions.create(model=model_to_use, messages=[sys] + messages, temperature=temp)
    return response.choices[0].message.content

def render_chat(key, is_sara=False):
    if key not in st.session_state: st.session_state[key] = []
    for msg in st.session_state[key]:
        with st.chat_message(msg["role"]):
            if msg.get("type") == "image": st.markdown(f'<img src="{msg["content"]}" style="width:100%;">', unsafe_allow_html=True)
            else: st.markdown(msg["content"])
            
    if prompt := st.chat_input("Ask..."):
        st.session_state[key].append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            if tool_mode and not is_sara:
                img_url = f"https://pollinations.ai/p/{urllib.parse.quote(prompt)}"
                st.markdown(f'<img src="{img_url}" style="width:100%;">', unsafe_allow_html=True)
                st.session_state[key].append({"role": "assistant", "content": img_url, "type": "image"})
            else:
                resp = get_response(st.session_state[key], is_sara)
                st.markdown(resp)
                st.session_state[key].append({"role": "assistant", "content": resp})
            st.rerun()

if mode == "𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰":
    st.title("𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰")
    render_chat("messages")
else:
    if 'auth' not in st.session_state: st.session_state['auth'] = False
    if not st.session_state['auth']:
        pwd = st.text_input("رمز:", type="password")
        if st.button("تایید ورود"):
            if pwd == "sara": st.session_state['auth'] = True; st.rerun()
    else:
        render_chat("sara_messages", is_sara=True)
        if st.button("خروج"): st.session_state['auth'] = False; st.rerun()
