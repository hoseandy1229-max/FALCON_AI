import streamlit as st
from groq import Groq
import urllib.parse
import random 
import base64

st.set_page_config(page_title="Falcon AI", layout="wide")

# استایل‌دهی مینیمال
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    [data-testid="stChatMessage"] { border: 1px solid #39FF14 !important; }
    </style>
""", unsafe_allow_html=True)

groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.title("𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰")

# سوئیچِ کوچک و مرتب در بالای چت
mode = st.radio(
    "حالتِ کاری:",
    ["💬 چت عادی", "🎨 تولید تصویر", "👁️ تحلیل عکس"],
    horizontal=True
)

if "messages" not in st.session_state: st.session_state.messages = []

# نمایش پیام‌ها
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image_gen": st.image(msg["content"])
        else: st.markdown(msg["content"])

# --- مدیریتِ حالت‌ها ---
# 1. حالت تحلیل عکس (اگر انتخاب شود، فایل‌لودر ظاهر می‌شود)
if mode == "👁️ تحلیل عکس":
    uploaded_file = st.file_uploader("عکس را اینجا آپلود کن تا تحلیلش کنم:", type=['jpg', 'png'])
    if uploaded_file:
        bytes_data = uploaded_file.read()
        base64_img = base64.b64encode(bytes_data).decode('utf-8')
        with st.chat_message("assistant"):
            with st.spinner("در حال تحلیل..."):
                res = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": "این عکس را به فارسی تحلیل کن"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                    ]}]
                ).choices[0].message.content
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})

# 2. کادر ارسال پیام (همیشه فعال است)
if prompt := st.chat_input("پیام یا دستور خود را بنویسید..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        if mode == "🎨 تولید تصویر":
            seed = random.randint(1, 999999)
            # اصلاح پرامپت
            final_p = "A realistic photo of the moon, 8k" if "ماه" in prompt else f"Real photo of {prompt}, 8k"
            url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(final_p)}?width=1024&height=1024&seed={seed}"
            st.image(url, caption="تصویر تولید شده")
            st.session_state.messages.append({"role": "assistant", "content": url, "type": "image_gen"})
        else:
            # چت عادی
            res = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": "کوتاه و فارسی پاسخ بده"}] + st.session_state.messages
            ).choices[0].message.content
            st.markdown(res)
            st.session_state.messages.append({"role": "assistant", "content": res})
    st.rerun()
