import streamlit as st
import subprocess, os, whisper, time
from gtts import gTTS
from deep_translator import GoogleTranslator

st.set_page_config(
    page_title="DubAI — AI Video Dubbing",
    page_icon="🎬",
    layout="centered"
)

# ---- Custom CSS ----
st.markdown("""
<style>
    .main { background-color: #0f0f1a; }
    .stApp { background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%); }
    h1 { color: #ffffff !important; font-size: 2.5rem !important; }
    h3 { color: #a0a0b0 !important; }
    .hero-box {
        background: linear-gradient(135deg, #6c63ff, #3b82f6);
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .hero-box h1 { font-size: 2.8rem !important; margin: 0; }
    .hero-box p { color: #e0e0ff; font-size: 1.1rem; margin-top: 0.5rem; }
    .feature-box {
        background: #1e1e3a;
        border: 1px solid #3333ff33;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 0.5rem 0;
        color: #ffffff;
    }
    .stButton > button {
        background: linear-gradient(135deg, #6c63ff, #3b82f6) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 2rem !important;
        font-size: 1.1rem !important;
        font-weight: bold !important;
        width: 100% !important;
        transition: all 0.3s !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(108, 99, 255, 0.4) !important;
    }
    .stProgress > div > div {
        background: linear-gradient(135deg, #6c63ff, #3b82f6) !important;
    }
    .stMultiSelect > div {
        background: #1e1e3a !important;
        border: 1px solid #6c63ff !important;
        border-radius: 10px !important;
    }
    .stFileUploader > div {
        background: #1e1e3a !important;
        border: 2px dashed #6c63ff !important;
        border-radius: 12px !important;
    }
    .success-box {
        background: linear-gradient(135deg, #00b09b, #96c93d);
        padding: 1rem 1.5rem;
        border-radius: 12px;
        color: white;
        font-weight: bold;
        text-align: center;
        margin: 1rem 0;
    }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ---- Hero Section ----
st.markdown("""
<div class="hero-box">
    <h1>🎬 DubAI</h1>
    <p>ইংরেজি ভিডিও → ৫ ভাষায় AI ডাবিং | সম্পূর্ণ ফ্রি</p>
</div>
""", unsafe_allow_html=True)

# ---- Features ----
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="feature-box">⚡ দ্রুত প্রসেসিং</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="feature-box">🌍 ৫টি ভাষা</div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="feature-box">💯 সম্পূর্ণ ফ্রি</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ---- Languages ----
LANGUAGES = {
    "🇧🇩 বাংলা":   "bn",
    "🇮🇳 হিন্দি":  "hi",
    "🇵🇰 উর্দু":   "ur",
    "🇹🇷 টার্কিশ": "tr",
    "🇸🇦 আরবি":    "ar",
}

# ---- Upload ----
st.markdown("### 📁 ভিডিও আপলোড করুন")
uploaded_file = st.file_uploader(
    "MP4, AVI বা MOV ফাইল drag & drop করুন",
    type=["mp4", "avi", "mov"]
)

st.markdown("### 🌍 ভাষা সিলেক্ট করুন")
selected_langs = st.multiselect(
    "",
    list(LANGUAGES.keys()),
    default=["🇧🇩 বাংলা"]
)

st.markdown("<br>", unsafe_allow_html=True)

# ---- Translate Function ----
def translate_text(text, lang_code):
    sentences = text.split('. ')
    chunks, current = [], ""
    for s in sentences:
        if len(current) + len(s) < 400:
            current += s + ". "
        else:
            chunks.append(current)
            current = s + ". "
    if current:
        chunks.append(current)
    parts = []
    for chunk in chunks:
        try:
            translated = GoogleTranslator(source='en', target=lang_code).translate(chunk)
            parts.append(translated if translated else chunk)
        except:
            parts.append(chunk)
    return ' '.join(parts)

# ---- Main Button ----
if st.button("🚀 ডাবিং শুরু করুন"):
    if not uploaded_file:
        st.error("⚠️ আগে ভিডিও আপলোড করুন!")
    elif not selected_langs:
        st.error("⚠️ কমপক্ষে একটি ভাষা সিলেক্ট করুন!")
    else:
        video_path = "/tmp/input_video.mp4"
        with open(video_path, "wb") as f:
            f.write(uploaded_file.read())

        progress = st.progress(0)
        status = st.empty()

        status.info("⏳ অডিও বের হচ্ছে...")
        subprocess.run(
            f'ffmpeg -i "{video_path}" -q:a 0 -map a /tmp/audio.mp3 -y',
            shell=True, capture_output=True
        )
        progress.progress(20)

        status.info("⏳ ইংরেজি টেক্সট বের হচ্ছে...")
        model = whisper.load_model("base")
        result = model.transcribe("/tmp/audio.mp3", language="en")
        english_text = result["text"]
        progress.progress(40)

        step = 60 // len(selected_langs)
        current_progress = 40

        st.markdown("### ⬇️ ডাউনলোড করুন")

        for lang_name in selected_langs:
            lang_code = LANGUAGES[lang_name]
            status.info(f"⏳ {lang_name} ডাবিং হচ্ছে...")

            translated = translate_text(english_text, lang_code)
            audio_path = f"/tmp/audio_{lang_code}.mp3"
            tts = gTTS(text=translated, lang=lang_code, slow=False)
            tts.save(audio_path)

            output_path = f"/tmp/dubbed_{lang_code}.mp4"
            subprocess.run(
                f'ffmpeg -i "{video_path}" -i {audio_path} '
                f'-c:v copy -map 0:v:0 -map 1:a:0 -shortest {output_path} -y',
                shell=True, capture_output=True
            )

            current_progress += step
            progress.progress(min(current_progress, 100))

            if os.path.exists(output_path):
                with open(output_path, "rb") as f:
                    st.download_button(
                        label=f"⬇️ {lang_name} ভিডিও ডাউনলোড",
                        data=f,
                        file_name=f"dubbed_{lang_code}.mp4",
                        mime="video/mp4",
                        key=lang_code
                    )

        progress.progress(100)
        status.empty()
        st.markdown('<div class="success-box">🎉 সব ডাবিং সম্পন্ন!</div>', unsafe_allow_html=True)

# ---- Footer ----
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align:center; color:#555577; font-size:0.85rem;'>
    Made with ❤️ | DubAI — Bangladesh's First AI Dubbing Tool
</div>
""", unsafe_allow_html=True)
