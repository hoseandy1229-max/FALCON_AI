import streamlit as st
from groq import Groq
from openai import OpenAI
import urllib.parse
import random 

st.set_page_config(page_title="Falcon AI", layout="wide")

# استایل‌دهی
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    [data-testid="stChatMessage"] { background-color: #000000 !important; border: 1px solid #39FF14 !important; }
    [data-testid="stChatMessage"] p { color: #39FF14 !important; }
    </style>
""", unsafe_allow_html=True)

# کلاینت‌ها
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"])

st.sidebar.title("تنظیمات")
models = {
    "Llama 3.3 70B (Groq)": {"client": "groq", "name": "llama-3.3-70b-versatile"},
    "Qwen 2.5 14B (Free)": {"client": "or", "name": "qwen/qwen-2.5-14b-instruct"}
}

selected_model_key = st.sidebar.selectbox("مدل:", list(models.keys()))
tool_mode = st.sidebar.checkbox("حالت تولید تصویر")
mode = st.sidebar.radio("بخش:", ["𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰", "𝑺𝑹 𝑩𝑶𝑻"])

def get_response(messages, is_sara=False):
    model_info = models[selected_model_key]
    if is_sara:
        sys = {"role": "system", "content": "تو دستیار شخصی سارا هستی. قوانین: اگر پاسخ تایید است با 'چشم بانو' شروع کن. فقط فارسی بنویس."}
        target_client = groq_client
        target_model = "llama-3.3-70b-versatile"
        temp = 0.2
    else:
        sys = {"role": "system", "content": "تو دستیار حرفه‌ای هستی. پاسخ‌های کوتاه و دقیق بده."}
        target_client = groq_client if model_info["client"] == "groq" else or_client
        target_model = model_info["name"]
        temp = 0.5
    
    try:
        response = target_client.chat.completions.create(model=target_model, messages=[sys] + messages, temperature=temp)
        return response.choices[0].message.content
    except Exception as e:
        return f"خطا در مدل: {str(e)}"

def render_chat(key, is_sara=False):
    if key not in st.session_state: st.session_state[key] = []
    for msg in st.session_state[key]:
        with st.chat_message(msg["role"]):
            if msg.get("type") == "image": 
                st.markdown(f"**نتیجه:**")
                st.image(msg["content"], caption="تصویر تولید شده")
                st.markdown(f"[📥 دانلود مستقیم]({msg['content']})")
            else: st.markdown(msg["content"])
            
    if prompt := st.chat_input("بنویس چی بسازم..."):
        st.session_state[key].append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            if tool_mode and not is_sara:
                random_seed = random.randint(1, 999999)
                
                # ترجمه و اصلاح هوشمندانه پرامپت
                if "درخت" in prompt and "خشک" in prompt:
                    final_prompt = "A detailed realistic photography of a dead, barren, lonely tree without any leaves in a desolate landscape, moody, cinematic lighting, 8k"
                elif "ماه" in prompt:
                    final_prompt = "A realistic, high-definition photo of the full moon in the night sky, cinematic, 8k, detailed"
                else:
                    final_prompt = f"Real photography of {prompt}, cinematic, 8k, realistic, highly detailed"
                
                safe_prompt = urllib.parse.quote(final_prompt)
                img_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=1024&nologo=true&seed={random_seed}"
                
                st.info("در حال عکاسی...")
                st.image(img_url, caption=f"تصویر برای: {prompt}")
                st.markdown(f"[📥 اگر تصویر لود نشد، برای دانلود مستقیم کلیک کنید]({img_url})")
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
