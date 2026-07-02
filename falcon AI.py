import streamlit as st
import google.generativeai as genai
import wikipedia
from PIL import Image

st.title("دستیار هوشمند فالکون")

# دریافت کلید از تنظیمات استریم‌لیت
api_key = st.secrets.get("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
    # استفاده از نسخه پایدار مدل
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = st.text_input("سوالی بپرس:")
    uploaded_file = st.file_uploader("عکس بفرست...", type=["jpg", "jpeg", "png"])

    if st.button("ارسال"):
        with st.spinner("در حال پردازش..."):
            try:
                if uploaded_file:
                    image = Image.open(uploaded_file)
                    response = model.generate_content([prompt or "این تصویر چیست؟", image])
                else:
                    response = model.generate_content(prompt)
                
                st.write(response.text)
            except Exception as e:
                st.error(f"خطا در اتصال به جمینای: {e}")
else:
    st.error("کلید API پیدا نشد. لطفاً در Secrets استریم‌لیت چک کن.")
