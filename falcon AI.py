import streamlit as st
from groq import Groq
from PIL import Image

# تنظیمات صفحه
st.set_page_config(page_title="فالکون ای‌آی", page_icon="🤖")

# استایل‌های پاستیلی
st.markdown("""
    <style>
    .stApp { background-color: #f0f8ff; } 
    .sara-box { background-color: #ffb7c5; padding: 20px; border-radius: 15px; border: 2px solid #add8e6; color: #555; }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 فالکون - دنیای دوگانه")

api_key = st.secrets.get("GROQ_API_KEY")
client = Groq(api_key=api_key)

# تب‌بندی
tab1, tab2 = st.tabs(["📢 بخش عمومی", "🌸 بخش اختصاصی سارا"])

# --- بخش عمومی ---
with tab1:
    st.write("سلام! اینجا بخش عمومی فالکون است. آماده‌ام به سوالاتت پاسخ بدهم.")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input("سوالی بپرس..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(model="llama-3.1-8b-instant", messages=st.session_state.messages, stream=True)
            response = st.write_stream(stream)
            st.session_state.messages.append({"role": "assistant", "content": response})

# --- بخش اختصاصی سارا ---
with tab2:
    st.markdown('<div class="sara-box">', unsafe_allow_html=True)
    password = st.text_input("رمز ورود برای سارا:", type="password")
    
    if password == "1234": # رمز را اینجا تغییر بده
        st.success("سلام سارا! به دنیای خصوصی‌ات خوش آمدی.")
        
        # آپلود تصویر
        uploaded_file = st.file_uploader("یک عکس برای فالکون بفرست...", type=["jpg", "png"])
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="تصویر ارسالی سارا", use_column_width=True)
            st.info("فالکون: عکس را دریافت کردم. منتظر توضیحاتت هستم!")
        
        # چت اختصاصی سارا
        if "sara_messages" not in st.session_state:
            st.session_state.sara_messages = [{"role": "system", "content": "تو دستیار اختصاصی سارا هستی. بسیار صمیمی و مهربان باش."}]
            
        if prompt_sara := st.chat_input("سوالی بپرس سارا جان..."):
            st.session_state.sara_messages.append({"role": "user", "content": prompt_sara})
            response = client.chat.completions.create(model="llama-3.1-8b-instant", messages=st.session_state.sara_messages)
            ans = response.choices[0].message.content
            st.write(f"🌸 فالکون: {ans}")
            st.session_state.sara_messages.append({"role": "assistant", "content": ans})
    else:
        st.warning("اینجا خلوتگاه ساراست... ورود برای بقیه ممنوع!")
    st.markdown('</div>', unsafe_allow_html=True)
