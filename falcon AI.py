import streamlit as st
from groq import Groq
import urllib.parse
import random 
import base64
from openai import OpenAI

st.set_page_config(page_title="Falcon AI", layout="wide")

# استایل‌دهی
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    [data-testid="stChatMessage"] { border: 1px solid #39FF14 !important; }
    </style>
""", unsafe_allow_html=True)

# کلاینت‌ها
try:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("خطا: کلید GROQ_API_KEY در secrets.toml یافت نشد.")
    st.stop()

st.title("𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰")

# سوئیچِ حالت
mode = st.radio(
    "حالتِ کاری:",
    ["💬 چت عادی", "🎨 تولید تصویر", "👁️ تحلیل عکس"],
    horizontal=True,
    key="mode_selector"
)

if "messages" not in st.session_state: st.session_state.messages = []
if "vision_active" not in st.session_state: st.session_state.vision_active = True

# نمایش پیام‌ها
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image_gen": st.image(msg["content"])
        else: st.markdown(msg["content"])

# --- مدیریتِ حالت‌ها ---
if mode == "👁️ تحلیل عکس":
    if not st.session_state.vision_active:
        st.warning("⚠️ توجه: طبق خطای قبلی، کلید API شما دسترسی به مدل Vision را ندارد. لطفاً از حالت‌های دیگر استفاده کنید.")
    else:
        uploaded_file = st.file_uploader("عکس را اینجا آپلود کن تا تحلیلش کنم:", type=['jpg', 'png'])
        if uploaded_file:
            bytes_data = uploaded_file.read()
            base64_img = base64.b64encode(bytes_data).decode('utf-8')
            with st.chat_message("assistant"):
                with st.spinner("در حال تحلیل با Llama 3.3 Vision..."):
                    try:
                        res = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": [
                                {"type": "text", "text": "این عکس را به فارسی تحلیل کن و بگو چه چیزی در آن می‌بینی."},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                            ]}]
                        ).choices[0].message.content
                        st.markdown(res)
                        st.session_state.messages.append({"role": "assistant", "content": res})
                    except groq.BadRequestError as e:
                        # --- مدیریت هوشمند خطا ---
                        st.error("❌ خطای دسترسی به مدل Vision. کلید API شما اجازه استفاده از این مدل را ندارد.")
                        st.markdown("این معمولاً به این دلیل است که کلید Groq شما در طرح رایگان است یا قابلیت Vision برای آن فعال نشده است.")
                        st.session_state.vision_active = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"خطای ناشناخته: {str(e)}")

# کادر ارسال پیام
if prompt := st.chat_input("پیام یا دستور خود را بنویسید..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        if mode == "🎨 تولید تصویر":
            seed = random.randint(1, 999999)
            final_p = "A realistic photo of the moon, 8k" if "ماه" in prompt else f"Real photo of {prompt}, 8k"
            url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(final_p)}?width=1024&height=1024&seed={seed}"
            st.image(url, caption="تصویر تولید شده")
            st.session_state.messages.append({"role": "assistant", "content": url, "type": "image_gen"})
        else:
            # چت عادی (استفاده از مدل Llama 3.3 70B که سریع است)
            try:
                res = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": "کوتاه و فارسی پاسخ بده"}] + st.session_state.messages
                ).choices[0].message.content
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})
            except Exception as e:
                st.error(f"خطای چت: {str(e)}")
    st.rerun()
