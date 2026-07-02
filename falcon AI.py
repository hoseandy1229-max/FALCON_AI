import streamlit as st
import google.generativeai as genai

st.title("تست نهایی اتصال")

api_key = st.secrets.get("GOOGLE_API_KEY")

if st.button("تست اتصال"):
    try:
        genai.configure(api_key=api_key)
        # استفاده از مدل به صورت رشته ساده
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("سلام")
        st.success("ارتباط با موفقیت برقرار شد!")
        st.write(response.text)
    except Exception as e:
        st.error(f"خطای اتصال: {e}")
