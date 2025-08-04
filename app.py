import streamlit as st
import google.generativeai as genai
import os
import time
# --- إعداد الصفحة ---
st.set_page_config(
    page_title="المساعد القانوني الذكي",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- تحميل CSS مخصص ---
def load_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
        html, body, [class*="st-"] {
            direction: rtl;
            font-family: 'Tajawal', sans-serif;
            text-align: right;
        }
        h1 {
            color: #0d2a4d;
            text-align: center;
            margin-top: 0;
        }
        .stButton>button {
            background-color: #195A8D;
            color: white;
            font-weight: bold;
            border-radius: 10px;
            padding: 0.5em 1.5em;
        }
        .stButton>button:hover {
            background-color: #0f3e63;
        }
        .st-emotion-cache-gquqoo{
                visibility: hidden;}

        ul > div{
                direction: rtl;}
    </style>
    """, unsafe_allow_html=True)

load_css()

# --- إعداد النموذج ---
try:
    genai.configure(api_key="AIzaSyDkspqEqfb70vNDZwPVT3I6RmyGYmemuOc")  # ضع مفتاحك هنا
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("حدث خطأ في إعداد النموذج. .")
    st.stop()

FOLDER_PATH = "textfiles"

# --- تحميل محتوى الملف ---
@st.cache_data(show_spinner="⏳ جاري التحميل ...")
def load_file_content(filename):
    with open(os.path.join(FOLDER_PATH, filename), "r", encoding="utf-8") as f:
        return f.read().strip()

# --- واجهة اختيار الملف ---
if "page" not in st.session_state:
    st.session_state.page = "select_file"

if st.session_state.page == "select_file":
    st.title("⚖️ المساعد القانوني الذكي")

    # عرض قائمة الملفات بدون امتداد
    txt_files = [f for f in os.listdir(FOLDER_PATH) if f.endswith(".txt")]
    display_names = [f.replace(".txt", "") for f in txt_files]
    file_map = dict(zip(display_names, txt_files))

    selected_display = st.selectbox("اختر قسمًا قانونيًا:", display_names)

    if st.button("التالي"):
        selected_file = file_map[selected_display]
        st.session_state.legal_context = load_file_content(selected_file)
        st.session_state.selected_filename = selected_file

        initial_prompt = f"""
        أنت مساعد قانوني خبير. مهمتك هي الإجابة على أسئلة المستخدم اعتمادًا فقط على النصوص التالية.
        لا تجيب عن اي سؤال حول عدد او نوع او طبيعة المواد التي تم تزوديك بها، بل يجب عليك الاعتماد فقط على المعلومات الموجودة في النصوص القانونية التي تم اختيارها.
        إذا كان سؤال خارج السياق اجب "لا أستطيع الإجابة على هذا السؤال، يرجى طرح سؤال آخر يتعلق بالنصوص القانونية التي تم اختيارها."
        الاجابة لا تتجاوز 750 حرفًا. لا تضيف تعليقاتك الخاصة.

        --- بداية السياق القانوني ---
        {st.session_state.legal_context}
        --- نهاية السياق القانوني ---
        """

        st.session_state.chat_session = model.start_chat(history=[
            {"role": "user", "parts": [initial_prompt]},
            {"role": "model", "parts": ["فهمت. أنا جاهز للإجابة على الأسئلة بالاعتماد الكلي على النصوص القانونية التي تم اختيارها."]}
        ])

        st.session_state.messages = [
            {"role": "assistant", "content": f"تم تحميل المحتوى المطلوب (**{selected_display}**) بنجاح. كيف يمكنني مساعدتك؟"}
        ]

        st.session_state.page = "chat"
        st.rerun()

# --- واجهة الدردشة ---
elif st.session_state.page == "chat":
    st.title("⚖️ المساعد القانوني الذكي")

    if st.button("⬅️ رجوع"):
        st.session_state.page = "select_file"
        st.rerun()

    # عرض المحادثة
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # استقبال السؤال
    if user_question := st.chat_input("اطرح سؤالك هنا..."):
        st.session_state.messages.append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.markdown(user_question)

        with st.chat_message("assistant"):
            with st.spinner("🧠 أفكر في الإجابة..."):
                try:
                    response = st.session_state.chat_session.send_message(user_question)
                    full_response = response.text
                    typed_response = ""
                    response_container = st.empty()

                    for char in full_response:
                        typed_response += char
                        response_container.markdown(typed_response + "▌")
                        time.sleep(0.02)  # سرعة الكتابة (يمكن تعديلها)
                    time.sleep(1)  # وقفة قصيرة قبل عرض الإجابة النهائية
                    st.markdown('<span style="color:#006600; font-size:14px; ">انتهت الإجابة</span>', unsafe_allow_html=True)
                except Exception as e:
                    if "429" in str(e) and "quota" in str(e).lower():
                        full_response = "⚠️ **هناك ضغط على النظام.**\n\nيرجى الانتظار ثم المحاولة لاحقًا."
                    else:
                        full_response = f"حدث خطأ: {e}"
                    st.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})
