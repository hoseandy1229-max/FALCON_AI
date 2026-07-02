import streamlit as st
import requests

st.title("فالکون - نسخه نهایی")

api_key = st.secrets.get("GOOGLE_API_KEY")
prompt = st.text_input("سوالی بپرس:")

if st.button("ارسال"):
    if not api_key:
        st.error("کلید API در تنظیمات نیست!")
    else:
        # استفاده از ورژن v1 به جای v1beta
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            
            if 'candidates' in result:
                st.write(result['candidates'][0]['content']['parts'][0]['text'])
            else:
                st.error(f"خطای گوگل: {result}")
        except Exception as e:
            st.error(f"خطای سیستم: {e}")
