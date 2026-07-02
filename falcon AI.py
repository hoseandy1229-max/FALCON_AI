import streamlit as st
import google.generativeai as genai

st.title("تست اتصال جمینای")

# ۱. چک کردن کلید API
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.error("کلید API در Secrets تنظیم نشده است!")
else:
    st.success("کلید API پیدا شد.")
    
    # ۲. تست اتصال به مدل
    try:
        genai.configure(api_key=api_key)
        # خط مربوط به مدل را به این شکل بنویس:
        model = genai.GenerativeModel('gemini-1.0-pro')


        
        if st.button("تست ارتباط با مدل"):
            response = model.generate_content("سلام، اگر این پیام را می‌بینی یعنی ارتباط برقرار است.")
            st.write("پاسخ مدل:", response.text)
    except Exception as e:
        st.error(f"خطا در اتصال به گوگل: {e}")
