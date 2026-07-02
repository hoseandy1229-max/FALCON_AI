import streamlit as st
import wikipedia
import os
import google.generativeai as genai

# تنظیمات اولیه
wikipedia.set_lang("fa")
st.set_page_config(page_title="Falcon AI", page_icon="🦅")

# مدیریت منعطف کلید API (اولویت با Secrets استریم‌لیت، سپس فایل .env)
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# منوی کناری و منطق شخصیت
st.sidebar.title("🦅 تنظیمات فالکون")
mode = st.sidebar.radio("حالت:", ["فالکون برای همه", "فالکونِ اختصاصی سارا"])

SECRET_PASSWORD = "sara" 
bg_color = "#0a0a0a"    # عمومی: مشکی
element_color = "#d4af37" # عمومی: طلایی
welcome_message = ""

system_instruction = "تو فالکونی، دستیاری باهوش و مرموز که عاشق تئوری‌های علمی و تاریخی هستی. کوتاه و با لحن جذاب جواب بده."

# منطق رمز و تم داینامیک برای سارا
if mode == "فالکونِ اختصاصی سارا":
    password = st.sidebar.text_input("رمز عبور:", type="password")
    if password == SECRET_PASSWORD:
        system_instruction = "تو فالکونی و در حال صحبت با سارا هستی. بسیار صمیمی، مهربان و با احترام زیاد جواب بده."
        bg_color = "#fce4ec"      # صورتی ملایم
        element_color = "#a2c2e8" # آبی پاستیلی
        welcome_message = "سارا، به سارا‌بات خوش اومدی! 🌸"
        
        st.sidebar.success("سلام سارای عزیز!")
        if "balloon_shown" not in st.session_state:
            st.balloons()
            st.session_state.balloon_shown = True
    else:
        system_instruction = "STOP"
else:
    st.session_state.balloon_shown = False

# تزریق CSS برای استایل‌دهی
st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_color}; }}
    h1 {{ color: {element_color}; text-align: center; }}
    .stChatMessage {{ border-radius: 15px; border: 1px solid {element_color}; }}
    </style>
    """, unsafe_allow_html=True)

# نمایش عنوان و پیام خوش‌آمدگویی
st.title("🦅 FALCON AI")
if welcome_message:
    st.markdown(f"<h3 style='text-align: center; color: #555;'>{welcome_message}</h3>", unsafe_allow_html=True)

# نمایش چت‌ها
if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# منطق پاسخ‌دهی
if prompt := st.chat_input("با فالکون صحبت کن..."):
    if system_instruction == "STOP":
        st.warning("رمز عبور اشتباه است یا وارد نشده!")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            # اگر کاربر درخواست تصویر داشت
            if "تصویر" in prompt or "عکس" in prompt:
                # جستجوی تصویر (بدون نیاز به اعتبار یا هزینه‌ی ای‌پی‌آی)
                image_url = f"https://source.unsplash.com/800x400/?{prompt}"
                st.image(image_url, caption="فالکون این را پیدا کرد")
                response = "اینم تصویری که خواستی!"
            else:
                # جستجوی متنی در ویکی‌پدیا و سپس هوش مصنوعی
                try:
                    search_results = wikipedia.summary(prompt, sentences=2)
                    response = f"🦅 [بررسی دانش]: {search_results}"
                except:
                    result = model.generate_content(system_instruction + prompt)
                    response = result.text
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})