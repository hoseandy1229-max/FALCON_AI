import streamlit as st
from groq import Groq
from openai import OpenAI
import urllib.parse
import random 
import base64

# تنظیمات صفحه
st.set_page_config(page_title="Falcon AI", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    [data-testid="stChatMessage"] { border: 1px solid #39FF14 !important; }
    </style>
""", unsafe_allow_html=True)

# کلاینت‌ها
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"])

st.title("𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰")

mode = st.radio("حالتِ کاری:", ["💬 چت عادی", "🎨 تولید تصویر", "👁️ تحلیل عکس"], horizontal=True)

if "messages" not in st.session_state: st.session_state.messages = []

# نمایش تاریخچه پیام‌ها
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image_gen": st.image(msg["content"])
        else: st.markdown(msg["content"])

# --- بخش تحلیل عکس با مکانیزمِ خودکارِ تغییرِ مدل ---
if mode == "👁️ تحلیل عکس":
    uploaded_file = st.file_uploader("عکس را آپلود کن:", type=['jpg', 'png', 'jpeg'])
    if uploaded_file:
        bytes_data = uploaded_file.read()
        base64_img = base64.b64encode(bytes_data).decode('utf-8')
        
        with st.chat_message("assistant"):
            with st.spinner("در حال جستجوی سرور آزاد..."):
                # لیست مدل‌های رایگان به ترتیب اولویت برای دور زدن شلوغی
                model_list = [
                    "mistralai/pixtral-12b:free",
                    "google/gemini-2.0-flash-lite-preview-02-05:free",
                    "qwen/qwen-2.5-vl-72b-instruct:free"
                ]
                
                success = False
                for model_name in model_list:
                    try:
                        response = or_client.chat.completions.create(
                            model=model_name,
                            messages=[{
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "این تصویر را دقیق و به فارسی تحلیل کن."},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                                ]
                            }],
                            max_tokens=400
                        )
                        res = response.choices[0].message.content
                        st.markdown(f"**تحلیل مدل ({model_name.split('/')[0]}):**\n\n{res}")
                        st.session_state.messages.append({"role": "assistant", "content": res})
                        success = True
                        break 
                    except Exception:
                        continue 
                
                if not success:
                    st.error("❌ تمامی سرورهای رایگان در حال حاضر به شدت شلوغ هستند.")
                    st.info("لطفاً چند دقیقه صبر کنید و دوباره امتحان کنید.")

# --- بخش چت و تولید تصویر ---
if prompt := st.chat_input("پیام یا دستور خود را بنویسید..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        if mode == "🎨 تولید تصویر":
            seed = random.randint(1, 999999)
            final_p = f"Real photo of {prompt}, 8k"
            url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(final_p)}?width=1024&height=1024&seed={seed}"
            st.image(url, caption="تصویر تولید شده")
            st.session_state.messages.append({"role": "assistant", "content": url, "type": "image_gen"})
        else:
            try:
                res = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": "کوتاه و فارسی پاسخ بده"}] + st.session_state.messages
                ).choices[0].message.content
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})
            except Exception as e:
                st.error("خطا در پاسخگویی سرور متن. دوباره تلاش کنید.")
    st.rerun()
