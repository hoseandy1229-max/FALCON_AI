import streamlit as st
import requests

st.title("فالکون (روش مستقیم)")

# کلید API را از Secrets بگیر
api_key = st.secrets.get("GOOGLE_API_KEY")

prompt = st.text_input("سوالی بپرس:")

if st.button("ارسال"):
    if not api_key:
        st.error("کلید API یافت نشد!")
    else:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            
            # نمایش جواب
            text_response = result['candidates'][0]['content']['parts'][0]['text']
            st.write(text_response)
        except Exception as e:
            st.error(f"خطا: {e}")
            st.write(result) # برای دیدن متن کامل خطا
