import streamlit as st
from groq import Groq
import urllib.parse

st.set_page_config(page_title="Falcon AI", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    [data-testid="stChatMessage"] { background-color: #000000 !important; border: 1px solid #39FF14 !important; }
    [data-testid="stChatMessage"] p { color: #39FF14 !important; }
    </style>
""", unsafe_allow_html=True)

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.sidebar.title("تنظیمات")
# اضافه شدن مدل‌های جدید و هوشمندتر
model_options = {
    "Llama 3.3 70B": "llama-3.3-70b-versatile",
    "Qwen 2.5 Coder 32B": "qwen-2.5-coder-32b",
    "Mixtral 8x7B": "mixtral-8x7b-32768"
}
selected_model_name = st.sidebar.selectbox("انتخاب مدل:", list(model_options.keys()))
tool_mode = st.sidebar.checkbox("تولید تصویر")
mode = st.sidebar.radio("بخش:", ["𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰", "𝑺𝑹 𝑩𝑶𝑻"])

def get_response(messages, is_sara=False):
    if is_sara:
        sys = {"role": "system", "content": "تو دستیار شخصی سارا هستی. قوانین: ۱. اگر پاسخ تایید است با 'چشم بانو' شروع کن. ۲. فقط فارسی بنویس. ۳. هیچ کاراکتر غیرفارسی استفاده نکن. ۴. پاسخ‌ها باید مستقیم و بدون حاشیه باشد."}
        model_to_use = "llama-3.3-70b-versatile"
        temp = 0.1 # بسیار سخت‌گیرانه
    else:
        sys = {"role": "system", "content": "تو دستیار حرفه‌ای هستی. پاسخ‌های منطقی، کوتاه و دقیق بده."}
        model_to_use = model_options[selected_model_name]
        temp = 0.3 # تمرکز بالا
    
    response = client.chat.completions.create(model=model_to_use, messages=[sys] + messages, temperature=temp)
    return response.choices[0].message.content

def render_chat(key, is_sara=False):
    if key not in st.session_state: st.session_state[key] = []
    for msg in st.session_state[key]:
        with st.chat_message(msg["role"]):
            if msg.get("type") == "image": st.markdown(f'<img src="{msg["content"]}" style="width:100%;">', unsafe_allow_html=True)
            else: st.markdown(msg["content"])
            
    if prompt := st.chat_input("Ask..."):
        st.session_state[key].append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            if tool_mode and not is_sara:
                img_url = f"https://pollinations.ai/p/{urllib.parse.quote(prompt)}"
                st.markdown(f'<img src="{img_url}" style="width:100%;">', unsafe_allow_html=True)
                st.session_state[key].append({"role": "assistant", "content": img_url, "type": "image"})
            else:
                resp = get_response(st.session_state[key], is_sara)
                st.markdown(resp)
                st.session_state[key].append({"role": "assistant", "content": resp})
            st.rerun()

if mode == "𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰":
    st.title("𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰")
    render_chat("messages")
else:
    if 'auth' not in st.session_state: st.session_state['auth'] = False
    if not st.session_state['auth']:
        pwd = st.text_input("رمز:", type="password")
        if st.button("تایید ورود"):
            if pwd == "sara": st.session_state['auth'] = True; st.rerun()
            else: st.error("رمز اشتباه است.")
    else:
        render_chat("sara_messages", is_sara=True)
        if st.button("خروج"): st.session_state['auth'] = False; st.rerun()
