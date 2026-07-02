import streamlit as st
import requests

st.title("فالکون - اتصال مستقیم")

api_key = st.secrets.get("GOOGLE_API_KEY")
prompt = st.text_input("سوالی بپرس:")

if st.button("ارسال"):
    if not api_key:
        st.error("کلید یافت نشد!")
    else:
        # آدرس جهانی و مستقیم بدون وابستگی به موقعیت جغرافیایی
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        try:
            # استفاده از یک درخواست مستقیم که کمتر از کتابخانه گوگل حساس است
            response = requests.post(url, headers=headers, json=data, timeout=10)
            result = response.json()
            
            if response.status_code == 200:
                st.write(result['candidates'][0]['content']['parts'][0]['text'])
            else:
                st.error(f"خطای سرویس: {result}")
        except Exception as e:
            st.error(f"خطای اتصال: {e}")
