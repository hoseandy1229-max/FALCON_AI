import streamlit as st
from groq import Groq

st.title("فالکون - نسخه Groq (پر سرعت)")

api_key = st.secrets.get("GROQ_API_KEY")
client = Groq(api_key=api_key)

prompt = st.text_input("سوالی بپرس:")

if st.button("ارسال"):
    if not api_key:
        st.error("کلید Groq پیدا نشد!")
    else:
        try:
            # استفاده از مدل llama3-8b که بسیار سریع و قدرتمند است
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
            )
            st.write(chat_completion.choices[0].message.content)
        except Exception as e:
            st.error(f"خطای Groq: {e}")
