import streamlit as st
import wikipedia
import os
import google.generativeai as genai
from PIL import Image

# تنظیمات اولیه
wikipedia.set_lang("fa")
st.set_page_config(page_title="𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰", page_icon="🦅")

# تنظیمات کلید API
api_key = st.secrets.get("GOOGLE_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# تنظیمات رابط کاربری و حالت سارا
st.sidebar.title("🦅 𝑭𝒂𝒍𝒄𝒐𝒏 𝑺𝒆𝒕𝒕𝒊𝒏𝒈")
mode = st.sidebar.radio("حالت:", ["𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰", "𝑺𝑹 𝑩𝑶𝑻"])

SECRET_PASSWORD = "sara" 
bg_color, element_color, welcome_message, system_instruction = "#0a0a0a", "#d4af37", "", "تو فالکونی، دستیاری باهوش و مرموز. کوتاه و جذاب جواب بده."

if mode == "𝑺𝑹 𝑩𝑶𝑻":
    if st.sidebar.text_input("رمز عبور:", type="password") == SECRET_PASSWORD:
        system_instruction = "تو فالکونی و در حال صحبت با سارا هستی. بسیار صمیمی، مهربان و با احترام زیاد جواب بده."
        bg_color, element_color, welcome_message = "#fce4ec", "#a2c2e8", "سارا، به سارا‌بات خوش اومدی! 🌸"
        if "balloon_shown" not in st.session_state:
            st.balloons()
            st.session_state.balloon_shown = True
    else:
        system_instruction = "STOP"

st.markdown(f"<style>.stApp {{ background-color: {bg_color}; }} h1 {{ color: {element_color}; }}</style>", unsafe_allow_html=True)
st.title("🦅 𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰")
if welcome_message: st.markdown(f"<h3 style='text-align: center;'>{welcome_message}</h3>", unsafe_allow_html=True)

# آپلود تصویر و چت
uploaded_file = st.file_uploader("𝑨𝑺𝑲 𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰", type=["jpg", "jpeg", "png"])

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("𝑨𝑺𝑲 𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰...
"):
    if system_instruction == "STOP":
        st.warning("رمز عبور اشتباه است!")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            response = ""
            try:
                # اولویت اول: تحلیل تصویر (اگر آپلود شد)
                if uploaded_file:
                    image = Image.open(uploaded_file)
                    st.image(image, caption="𝒀𝒐𝒖𝒓 𝑰𝒎𝒂𝒈𝒆")
                    result = model.generate_content([system_instruction + prompt, image])
                    response = result.text
                else:
                    # اولویت دوم: هوش مصنوعی (جمینای)
                    result = model.generate_content(system_instruction + prompt)
                    response = result.text
            except:
                # اولویت سوم: ویکی‌پدیا
                try:
                    response = f"🦅 [بررسی دانش]: {wikipedia.summary(prompt, sentences=2)}"
                except:
                    response = "متأسفم، پاسخی ندارم."
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
