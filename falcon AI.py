import streamlit as st
import google.generativeai as genai

st.title("تست اتصال نهایی")

api_key = st.secrets.get("GOOGLE_API_KEY")

if st.button("تست اتصال"):
    try:
        genai.configure(api_key=api_key)
        
        # لیست کردن مدل‌ها برای دیدن اینکه چه چیزی در دسترس است
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        st.write("مدل‌های در دسترس:", available_models)
        
        # استفاده از اولین مدل موجود در لیست به جای نام‌گذاری دستی
        model = genai.GenerativeModel(available_models[0])
        response = model.generate_content("سلام")
        st.success(f"اتصال برقرار شد با مدل: {available_models[0]}")
        st.write(response.text)
        
    except Exception as e:
        st.error(f"خطای اتصال: {e}")
