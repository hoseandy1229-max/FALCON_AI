import streamlit as st
from groq import Groq
import urllib.parse

st.set_page_config(page_title="Falcon AI", layout="wide")

# استایل‌دهی: حباب مشکی و متن سبز فسفوری
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    [data-testid="stChatMessage"] { background-color: #000000 !important; border: 1px solid #39FF14 !important; }
    [data-testid="stChatMessage"] p { color: #39FF14 !important; }
    </style>
""", unsafe_allow_html=True)

api_key = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=api_key)

# توابع پاسخ‌دهی
def get_falcon_response(messages):
    system_instruction = {"role": "system", "content": "دستیار دقیق و حرفه‌ای. تعارف نکن."}
    response = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[system_instruction] + messages)
    return response.choices[0].message.content

def get_sara_response(messages):
    system_instruction = {"role": "system", "content": "تو دستیارِ سارا هستی. بسیار محترمانه صحبت کن. در ابتدای هر پاسخ بگو: 'چشم بانو'. از هذیان‌گویی بپرهیز و پاسخ‌های دقیق و کوتاه بده."}
    response = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[system_instruction] + messages)
    return response.choices[0].message.content

# تابع نمایش چت
def render_chat(key, is_sara=False):
    if key not in st.session_state: st.session_state[key] = []
    
    for msg in st.session_state[key]:
        with st.chat_message(msg["role"]):
            if msg.get("type") == "image":
                st.markdown(f'<img src="{msg["content"]}" style="width:100%;">', unsafe_allow_html=True)
            else:
                st.markdown(msg["content"])
            
    input_text = "𝑨𝒔𝒌 𝑴𝒚 𝑸𝒖𝒆𝒆𝒏" if is_sara else "𝑨𝒔𝒌 𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰"
    if prompt := st.chat_input(input_text):
        st.session_state[key].append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            if tool_mode and not is_sara:
                encoded_prompt = urllib.parse.quote(prompt)
                img_url = f"https://pollinations.ai/p/{encoded_prompt}"
                st.markdown(f'<img src="{img_url}" style="width:100%;">', unsafe_allow_html=True)
                st.session_state[key].append({"role": "assistant", "content": img_url, "type": "image"})
            else:
                resp = get_sara_response(st.session_state[key]) if is_sara else get_falcon_response(st.session_state[key])
                st.markdown(resp)
                st.session_state[key].append({"role": "assistant", "content": resp})
            st.rerun()

# منوی کناری
st.sidebar.title("تنظیمات پنل")
if st.sidebar.button("Reset"): st.session_state.clear(); st.rerun()
mode = st.sidebar.radio("بخش:", ["𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰", "𝑺𝑹 𝑩𝑶𝑻"])
tool_mode = st.sidebar.checkbox("حالت تولید تصویر")

# اجرای بدنه اصلی
if mode == "𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰":
    st.title("𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰")
    render_chat("messages")
else:
    if 'auth' not in st.session_state: st.session_state['auth'] = False
    if not st.session_state['auth']:
        st.title("🌸 مخصوص سارا")
        if st.text_input("رمز:", type="password") == "sara":
            st.session_state['auth'] = True
            st.rerun()
    else:
        tab1, tab2, tab3 = st.tabs(["💬 چت", "🖼️ گالری", "⚙️ تنظیمات"])
        with tab1: render_chat("sara_messages", is_sara=True)
        with tab2: st.write("گالری در حال توسعه...")
        with tab3:
            if st.button("خروج از محیط سارا"): st.session_state['auth'] = False; st.rerun()
