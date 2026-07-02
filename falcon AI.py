import streamlit as st
import google.generativeai as genai
import wikipedia
from PIL import Image

# تنظیمات کتابخانه ویکی‌‌پدیا
wikipedia.set_lang("fa")

# تنظیمات کلید API
api_key = st.secrets.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("کلید API در تنظیمات پیدا نشد!")

st.title("🦅 𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰 - Vision")

# آپلود تصویر
uploaded_file = st.file_uploader("𝑨𝑺𝑲 𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰", type=["jpg", "jpeg", "png"])

# مدیریت تاریخچه چت
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ورودی متن
if prompt := st.chat_input("𝑨𝑺𝑲 𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        full_response = ""
        
        try:
            # اگر تصویر وجود داشته باشد، آن را به جمینای می‌فرستیم
            if uploaded_file:
                image = Image.open(uploaded_file)
                st.image(image, caption="𝑳𝒐𝒂𝒅𝒊𝒏𝒈")
                response = model.generate_content([prompt, image])
            else:
                # اولویت اول: جمینای برای متن
                response = model.generate_content(prompt)
            
            full_response = response.text
            
        except:
            # اولویت دوم: ویکی‌‌پدیا اگر جمینای خطا داد
            try:
                summary = wikipedia.summary(prompt, sentences=2)
                full_response = f"پاسخی از مدل دریافت نشد، اما این اطلاعات را در ویکی‌‌پدیا یافتم: \n\n{summary}"
            except:
                full_response = "متأسفم، در حال حاضر پاسخی برای این سوال ندارم."
        
        st.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
