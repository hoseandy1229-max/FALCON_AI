import streamlit as st
from groq import Groq
import urllib.parse

st.set_page_config(page_title="Falcon AI", layout="wide")

# استایل‌دهی جدید: حباب‌های مشکی و متن سبز فسفوری
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .sara-bg { background-color: #ffe4e6 !important; padding: 20px; border-radius: 20px; color: black; }
    
    /* حباب‌های چت مشکی با متن سبز فسفوری */
    [data-testid="stChatMessage"] {
        background-color: #000000 !important;
        border: 1px solid #39FF14 !important;
        color: #39FF14 !important;
    }
    /* رنگ متن داخل حباب */
    [data-testid="stChatMessage"] p {
        color: #39FF14 !important;
    }
    </style>
""", unsafe_allow_html=True)

# تنظیمات کلاینت
api_key = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=api_key)

# منوی کناری
st.sidebar.title("تنظیمات پنل")
if st.sidebar.button("Reset"):
    st.session_state.clear()
    st.rerun()

mode = st.sidebar.radio("بخش:", ["𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰", "𝑺𝑹 𝑩𝑶𝑻"])
tool_mode = st.sidebar.checkbox("حالت تولید تصویر (Image Generator)")

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
        with st.chat_message(msg["role"]):
            if msg.get("type") == "image":
                st.image(msg["content"], use_container_width=True)
            else:
                st.markdown(msg["content"])
            
    if prompt := st.chat_input("𝑨𝒔𝒌 𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰"):
        st.session_state[key].append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            if tool_mode:
                encoded_prompt = urllib.parse.quote(prompt)
                img_url = f"https://pollinations.ai/p/{encoded_prompt}"
                st.image(img_url, use_container_width=True)
                st.session_state[key].append({"role": "assistant", "content": img_url, "type": "image"})
            else:
                resp = get_response(st.session_state[key])
                st.markdown(resp)
                st.session_state[key].append({"role": "assistant", "content": resp})
            st.rerun()

if mode == "𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰":
    st.title("𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰")
    render_chat("messages")
else:
    st.markdown('<div class="sara-bg">', unsafe_allow_html=True)
    st.title("🌸 مخصوص سارا")
    if st.text_input("رمز:", type="password") == "sara":
        render_chat("sara_messages")
    else:
        st.warning("قفل است.")
    st.markdown('</div>', unsafe_allow_html=True)
