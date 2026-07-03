import streamlit as st
from groq import Groq
from openai import OpenAI
import urllib.parse

st.set_page_config(page_title="Falcon AI", layout="wide")

# استایل‌دهی (بهبود یافته برای نمایش تصاویر)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    img { border-radius: 10px; border: 2px solid #39FF14; }
    </style>
""", unsafe_allow_html=True)

# تنظیم کلاینت‌ها
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"])

st.sidebar.title("تنظیمات")
# مدل‌های تست شده و پایدار
models = {
    "Llama 3.3 70B (Groq)": {"client": "groq", "name": "llama-3.3-70b-versatile"},
    "Qwen 2.5 14B (Free)": {"client": "or", "name": "qwen/qwen-2.5-14b-instruct"},
    "Mistral Nemo 12B (Free)": {"client": "or", "name": "mistralai/mistral-nemo"}
}

selected_model_key = st.sidebar.selectbox("انتخاب مدل:", list(models.keys()))
tool_mode = st.sidebar.checkbox("حالت تولید تصویر")
mode = st.sidebar.radio("بخش:", ["𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰", "𝑺𝑹 𝑩𝑶𝑻"])

def get_response(messages, is_sara=False):
    model_info = models[selected_model_key]
    sys = {"role": "system", "content": "تو دستیار شخصی سارا هستی. فقط فارسی، کوتاه، بدون حاشیه."} if is_sara else {"role": "system", "content": "تو دستیار حرفه‌ای هستی."}
    
    target_client = groq_client if is_sara or model_info["client"] == "groq" else or_client
    target_model = "llama-3.3-70b-versatile" if is_sara else model_info["name"]
    
    try:
        response = target_client.chat.completions.create(model=target_model, messages=[sys] + messages, temperature=0.3)
        return response.choices[0].message.content
    except Exception as e:
        return f"خطای مدل: {str(e)[:30]}"

def render_chat(key, is_sara=False):
    if key not in st.session_state: st.session_state[key] = []
    for msg in st.session_state[key]:
        with st.chat_message(msg["role"]):
            if msg.get("type") == "image": 
                st.image(msg["content"], use_container_width=True)
            else: st.markdown(msg["content"])
            
    if prompt := st.chat_input("Ask..."):
        st.session_state[key].append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            if tool_mode and not is_sara:
                # استفاده از تابع image استریم‌لیت به جای تگ HTML برای پایداری بیشتر
                img_url = f"https://pollinations.ai/p/{urllib.parse.quote(prompt)}?width=512&height=512&seed=42"
                st.image(img_url, caption="تصویر تولید شده", use_container_width=True)
                st.session_state[key].append({"role": "assistant", "content": img_url, "type": "image"})
            else:
                resp = get_response(st.session_state[key], is_sara)
                st.markdown(resp)
                st.session_state[key].append({"role": "assistant", "content": resp})
            st.rerun()

# بقیه بخش‌ها (if mode == ... و غیره) دقیقاً مثل قبل باقی می‌ماند.
