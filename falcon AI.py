import streamlit as st
from groq import Groq
from PIL import Image

# تنظیمات ظاهری (تم مشکی و شیک)
st.set_page_config(page_title="Falcon AI", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .sara-box { background-color: #1e1e2e; padding: 25px; border-radius: 20px; border: 2px solid #ffb7c5; }
    </style>
""", unsafe_allow_html=True)

# سایدبار
with st.sidebar:
    st.title("🤖 Falcon Control")
    mode = st.radio("انتخاب بخش:", ["📢 عمومی", "🌸 بخش سارا"])
    st.divider()
    st.write("نسخه پرسرعت Groq - نسخه 3.1")

api_key = st.secrets.get("GROQ_API_KEY")
client = Groq(api_key=api_key)

# --- بخش عمومی ---
if mode == "📢 عمومی":
    st.title("📢 فالکون عمومی")
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
            chat_completion = client.chat.completions.create(model="llama-3.1-8b-instant", messages=st.session_state.messages)
            response = chat_completion.choices[0].message.content
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# --- بخش اختصاصی سارا ---
else:
    st.title("🌸 خلوتگاه سارا")
    st.markdown('<div class="sara-box">', unsafe_allow_html=True)
    password = st.text_input("رمز عبور:", type="password")
    
    if password == "1234": # رمز خودت را اینجا بگذار
        st.success("سلام سارا، به دنیای شخصی خوش آمدی.")
        
        uploaded_file = st.file_uploader("ارسال تصویر برای فالکون...", type=["jpg", "png"])
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="تصویر سارا", width=300)
            st.info("فالکون: عکسی که فرستادی را دیدم!")

        if "sara_messages" not in st.session_state:
            st.session_state.sara_messages = [{"role": "system", "content": "تو دستیار اختصاصی سارا هستی. بسیار صمیمی و مهربان باش."}]
            
        if prompt_sara := st.chat_input("سارا جان، چی می‌خوای بپرسی؟"):
            st.session_state.sara_messages.append({"role": "user", "content": prompt_sara})
            response = client.chat.completions.create(model="llama-3.1-8b-instant", messages=st.session_state.sara_messages)
            ans = response.choices[0].message.content
            st.write(f"🌸 فالکون: {ans}")
            st.session_state.sara_messages.append({"role": "assistant", "content": ans})
    else:
        st.warning("اینجا ورود برای دیگران ممنوع است!")
    st.markdown('</div>', unsafe_allow_html=True)
