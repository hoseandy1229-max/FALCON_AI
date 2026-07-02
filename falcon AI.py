import streamlit as st
import requests

st.title("فالکون (تست نهایی)")

api_key = st.secrets.get("GOOGLE_API_KEY")
prompt = st.text_input("سوالی بپرس:")

if st.button("ارسال"):
    if not api_key:
        st.error("کلید API یافت نشد!")
    else:
        # تغییر در URL: استفاده از gemini-pro به جای gemini-1.5-flash
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            
            # نمایش جواب با مدیریت خطا
            if 'candidates' in result:
                st.write(result['candidates'][0]['content']['parts'][0]['text'])
            else:
                st.error(f"خطای گوگل: {result}")
        except Exception as e:
            st.error(f"خطای سیستم: {e}")
