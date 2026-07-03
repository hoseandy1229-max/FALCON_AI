import streamlit as st
from groq import Groq
from openai import OpenAI
import urllib.parse
import random 
import base64

st.set_page_config(page_title="Falcon AI", layout="wide")

# --- استایل‌دهی پیشرفته (شامل آیکون‌های شناور) ---
st.markdown("""
    <style>
    /* استایل کلی */
    .stApp { background-color: #0e1117; color: white; }
    [data-testid="stChatMessage"] { background-color: #000000 !important; border: 1px solid #39FF14 !important; }
    [data-testid="stChatMessage"] p { color: #39FF14 !important; }
    
    /* تنظیمات کادر چت اصلی */
    .stChatInputContainer {
        padding-bottom: 20px; /* فاصله برای دکمه‌ها */
    }
    
    /* کانتینر دکمه‌های شناور پایین صفحه */
    .floating-container {
        position: fixed;
        bottom: 80px; /* فاصله از پایین صفحه */
        right: 30px;   /* فاصله از راست */
        display: flex;
        flex-direction: column; /* دکمه‌ها زیر هم */
        gap: 10px;
        z-index: 100;
    }
    
    /* استایل دکمه‌های شناور */
    .float-btn {
        background-color: #39FF14;
        color: #000000;
        border: none;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        font-size: 24px;
        cursor: pointer;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
    }
    
    .float-btn:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 12px rgba(0,0,0,0.5);
        background-color: #aaff80;
    }
    
    /* استایل راهنمای کوچک کنار دکمه */
    .btn-tooltip {
        position: absolute;
        right: 60px;
        background-color: rgba(0,0,0,0.8);
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 12px;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.3s ease;
    }
    
    .float-btn:hover .btn-tooltip {
        opacity: 1;
    }
    </style>
""", unsafe_allow_html=True)

# کلاینت‌ها
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"])

st.sidebar.title("تنظیمات")
models = {
    "Llama 3.3 70B (Vision)": {"client": "groq", "name": "llama-3.3-70b-versatile"},
    "Qwen 2.5 14B (Text Only)": {"client": "or", "name": "qwen/qwen-2.5-14b-instruct"}
}

selected_model_key = st.sidebar.selectbox("مدل:", list(models.keys()))
mode = st.sidebar.radio("بخش:", ["𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰", "𝑺𝑹 𝑩𝑶𝑻"])

# متغیرهای Session State
if "active_tool" not in st.session_state: st.session_state.active_tool = "chat"
if "analysis_result" not in st.session_state: st.session_state.analysis_result = None
if "generated_image_url" not in st.session_state: st.session_state.generated_image_url = None
if "user_uploaded_img_base64" not in st.session_state: st.session_state.user_uploaded_img_base64 = None

def analyze_image_base64(base64_data):
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "لطفاً این تصویر را به فارسی تحلیل کن و بگو چه چیزی در آن می‌بینی."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_data}"}}
                    ]
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.5
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"خطا در تحلیل تصویر: {str(e)}"

# تابع اصلی چت
def render_chat(key, is_sara=False):
    if key not in st.session_state: st.session_state[key] = []
    for msg in st.session_state[key]:
        with st.chat_message(msg["role"]):
            if msg.get("type") == "image_gen":
                st.markdown(f"**تصویر تولید شده:**")
                st.image(msg["content"], caption="نتیجه")
            elif msg.get("type") == "image_user":
                st.markdown(f"**تصویر آپلود شده:**")
                st.image(msg["content"], width=300)
            else:
                st.markdown(msg["content"])

    # --- مدیریتِ ابزارها (آپلود یا تولید) ---
    
    # اگر کاربر در حالتِ آپلود عکس است، یک فایل‌لودرِ اختصاصی در چت باز می‌شود
    if st.session_state.active_tool == "upload" and not is_sara:
        st.info("🔧 حالت تحلیل تصویر فعال است. لطفاً عکس خود را انتخاب کنید.")
        uploaded_file = st.file_uploader("انتخاب تصویر برای تحلیل...", type=['png', 'jpg', 'jpeg'])
        
        if uploaded_file:
            # تبدیل تصویر به base64
            bytes_data = uploaded_file.read()
            base64_data = base64.b64encode(bytes_data).decode('utf-8')
            
            with st.chat_message("user"):
                 st.markdown("**تصویر آپلود شد.**")
                 st.image(uploaded_file, width=300)
                 st.session_state[key].append({"role": "user", "content": base64_data, "type": "image_user"})

            with st.chat_message("assistant"):
                with st.spinner("در حال تحلیل تصویر... هوش مصنوعی Llama 3.3 Vision در حال پردازش است."):
                     analysis = analyze_image_base64(base64_data)
                     st.markdown(analysis)
                     st.session_state[key].append({"role": "assistant", "content": analysis})
            
            # بازگشت به حالت عادی پس از تحلیل
            st.session_state.active_tool = "chat"
            st.rerun()

    # --- کادرِ ورودیِ اصلی (چت و تولید تصویر) ---
    prompt = st.chat_input("Ask... یا از منوهای سمت راست استفاده کنید")
    
    if prompt:
        st.session_state[key].append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            if st.session_state.active_tool == "gen_img" and not is_sara:
                # حالت تولید تصویر
                random_seed = random.randint(1, 999999)
                
                if "ماه" in prompt:
                    final_prompt = "A realistic, high-definition photo of the full moon in the night sky, cinematic, 8k, detailed"
                elif "درخت" in prompt and "خشک" in prompt:
                     final_prompt = f"Highly detailed photography of a lonely dead, barren tree with intricate branches, no leaves, moody atmosphere"
                else:
                    final_prompt = f"Real photography of {prompt}, cinematic, 8k, realistic, highly detailed"
                
                safe_prompt = urllib.parse.quote(final_prompt)
                img_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=1024&nologo=true&seed={random_seed}"
                
                st.info("در حال تولید/طراحی توسط هوش مصنوعی...")
                st.image(img_url, caption=f"تصویر برای: {prompt}")
                st.markdown(f"[📥 اگر تصویر لود نشد، برای دانلود کلیک کنید]({img_url})")
                st.session_state[key].append({"role": "assistant", "content": img_url, "type": "image_gen"})
                
                # بازگشت به حالت عادی پس از تولید
                st.session_state.active_tool = "chat"
            else:
                # حالت پاسخگویی متنی (مدل Groq یا OpenRouter)
                model_info = models[selected_model_key]
                if is_sara:
                    sys = {"role": "system", "content": "تو دستیار شخصی سارا هستی. قوانین: اگر پاسخ تایید است با 'چشم بانو' شروع کن. فقط فارسی بنویس."}
                    target_client = groq_client
                    target_model = "llama-3.3-70b-versatile"
                else:
                    sys = {"role": "system", "content": "تو دستیار حرفه‌ای هستی. پاسخ‌های کوتاه و دقیق بده."}
                    target_client = groq_client if model_info["client"] == "groq" else or_client
                    target_model = model_info["name"]
                
                try:
                    response = target_client.chat.completions.create(model=target_model, messages=[sys] + st.session_state[key], temperature=0.5)
                    ans = response.choices[0].message.content
                    st.markdown(ans)
                    st.session_state[key].append({"role": "assistant", "content": ans})
                except Exception as e:
                    st.error(f"خطا: {str(e)}")
        st.rerun()

# --- لاجیکِ دکمه‌هایِ شناور (اینترفیس اصلی) ---
if mode == "𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰":
    st.title("𝑭𝑨𝑳𝑪𝑶𝑵 𝑨𝑰")
    
    # تزریق دکمه‌های شناور با HTML/CSS سفارشی
    st.markdown("""
        <div class="floating-container">
            <a href="?tool=upload" class="float-btn" title="آپلود تصویر">
                📎
                <span class="btn-tooltip">آپلود و تحلیل عکس</span>
            </a>
            <a href="?tool=gen_img" class="float-btn" title="تولید تصویر">
                🎨
                <span class="btn-tooltip">تولید عکس از متن</span>
            </a>
        </div>
    """, unsafe_allow_html=True)
    
    # بررسی اینکه کاربر روی کدام دکمه کلیک کرده است
    query_params = st.query_params
    if "tool" in query_params:
        tool = query_params["tool"]
        if tool == "upload":
            st.session_state.active_tool = "upload"
            st.rerun() # رفرش فوری برای نمایش فایل‌لودر
        elif tool == "gen_img":
            st.session_state.active_tool = "gen_img"
            st.rerun() # رفرش فوری برای تغییر راهنمای کادر چت

    render_chat("messages")
else:
    # بخش سارا (SR BOT) - دکمه‌های شناور ندارد
    if 'auth' not in st.session_state: st.session_state['auth'] = False
    if not st.session_state['auth']:
        pwd = st.text_input("رمز:", type="password")
        if st.button("تایید ورود"):
            if pwd == "sara": st.session_state['auth'] = True; st.rerun()
            else: st.error("رمز اشتباه است.")
    else:
        render_chat("sara_messages", is_sara=True)
        if st.button("خروج"): st.session_state['auth'] = False; st.rerun()

# مدیریت وضعیت "حالت فعال" بین رفرش‌ها
if st.session_state.active_tool == "upload" and not st.file_uploader:
    pass # اگر در حالت آپلود بودیم و فایلی انتخاب نشد، حالت را حفظ می‌کنیم تا کاربر عکس را انتخاب کند
