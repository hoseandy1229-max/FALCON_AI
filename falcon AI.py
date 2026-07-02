import streamlit as st
import google.generativeai as genai

st.title("فالکون - نسخه تستِ آخر")

# استفاده از Secrets
api_key = st.secrets.get("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
    # تغییر به نسخه پایدارتر gemini-1.0-pro
    model = genai.GenerativeModel('gemini-1.0-pro')
    
    prompt = st.text_input("سوالی بپرس:")
    if st.button("ارسال"):
        try:
            response = model.generate_content(prompt)
            st.write(response.text)
        except Exception as e:
            st.error(f"خطای جمینای: {e}")
else:
    st.error("کلید API در Secrets نیست!")
