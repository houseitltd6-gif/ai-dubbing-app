import streamlit as st
import subprocess, os, whisper, time
from gtts import gTTS
from deep_translator import GoogleTranslator

st.set_page_config(
    page_title="DubIT — AI Video Dubbing",
    page_icon="🎬",
    layout="centered"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

* { font-family: 'Inter', sans-serif; }

.stApp {
    background: #080812;
}

/* Hero */
.hero {
    background: linear-gradient(135deg, #1a0533 0%, #0d1b4b 50%, #001a3a 100%);
    border: 1px solid rgba(139, 92, 246, 0.3);
    border-radius: 24px;
    padding: 3rem 2rem;
    text-align: center;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(139,92,246,0.15) 0%, transparent 60%);
}
.hero-badge {
    display: inline-block;
    background: rgba(139, 92, 246, 0.2);
    border: 1px solid rgba(139, 92, 246, 0.5);
    color: #a78bfa;
    padding: 0.3rem 1rem;
    border-radius: 50px;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 1rem;
}
.hero h1 {
    font-size: 3.5rem !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #ffffff 0%, #a78bfa 50%, #60a5fa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0.5rem 0 !important;
    line-height: 1.1 !important;
}
.hero p {
    color: #94a3b8;
    font-size: 1.1rem;
    margin: 0;
}

/* Stats */
.stats-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
}
.stat-card {
    flex: 1;
    background: linear-gradient(135deg, #0f0f1f, #1a1a35);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 16px;
    padding: 1.2rem;
    text-align: center;
    transition: all 0.3s;
}
.stat-card:hover {
    border-color: rgba(139, 92, 246, 0.6);
    transform: translateY(-3px);
    box-shadow: 0 10px 30px rgba(139, 92, 246, 0.2);
}
.stat-number {
    font-size: 1.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.stat-label {
    color: #64748b;
    font-size: 0.8rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Section */
.section-title {
    color: #e2e8f0;
    font-size: 1rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Upload area */
.stFileUploader > div {
    background: linear-gradient(135deg, #0f0f1f, #1a1a35) !important;
    border: 2px dashed rgba(139, 92, 246, 0.4) !important;
    border-radius: 16px !important;
    transition: all 0.3s !important;
}
.stFileUploader > div:hover {
    border-color: rgba(139, 92, 246, 0.8) !important;
    box-shadow: 0 0 30px rgba(139, 92, 246, 0.15) !important;
}

/* Multiselect */
.stMultiSelect > div > div {
    background: #0f0f1f !important;
    border: 1px solid rgba(139, 92, 246, 0.3) !important;
    border-radius: 12px !important;
}

/* Button */
.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #2563eb) !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 1rem 2rem !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    width: 100% !important;
    letter-spacing: 0.5px !important;
    transition: all 0.3s !important;
    box-shadow: 0 4px 20px rgba(124, 58, 237, 0.4) !important;
}
.stButton > button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 8px 35px rgba(124, 58, 237, 0.6) !important;
}

/* Progress */
.stProgress > div > div {
    background: linear-gradient(135deg, #7c3aed, #2563eb) !important;
    border-radius: 10px !important;
}

/* Download button */
.stDownloadButton > button {
    background: linear-gradient(135deg, #065f46, #047857) !important;
    color: white !important;
    border: 1px solid rgba(16, 185, 129, 0.3) !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    width: 100% !important;
    transition: all 0.3s !important;
}
.stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(16, 185, 129, 0.3) !important;
}

/* Info/Success boxes */
.stAlert {
    border-radius: 12px !important;
    border: none !important;
}

/* Footer */
.footer {
    text-align: center;
    padding: 2rem 0 1rem;
    border-top: 1px solid rgba(139, 92, 246, 0.1);
    margin-top: 2rem;
}
.footer-brand {
    font-size: 1rem;
    font-weight: 700;
    background: linear-gradient(135deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.footer-sub {
    color: #334155;
    font-size: 0.8rem;
    margin-top: 0.3rem;
}

footer { visibility: hidden; }
#MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ---- HERO ----
st.markdown("""
<div class="hero">
    <div class="hero-badge">🇧🇩 Bangladesh's First</div>
    <h1>DubIT</h1>
    <p>ইংরেজি ভিডিও → ৫ ভাষায় AI ডাবিং | সম্পূর্ণ ফ্রি</p>
</div>
""", unsafe_allow_html=True)

# ---- STATS ----
st.markdown("""
<div class="stats-row">
    <div class="stat-card">
        <div class="stat-number">5+</div>
        <div class="stat-label">ভাষা</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">AI</div>
        <div class="stat-label">পাওয়ার্ড</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">FREE</div>
        <div class="stat-label">সম্পূর্ণ ফ্রি</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">200MB</div>
        <div class="stat-label">ফাইল লিমিট</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---- LANGUAGES ----
LANGUAGES = {
    "🇧🇩 বাংলা":   "bn",
    "🇮🇳 হিন্দি":  "hi",
    "🇵🇰 উর্দু":   "ur",
    "🇹🇷 টার্কিশ": "tr",
    "🇸🇦 আরবি":    "ar",
}

# ---- UPLOAD ----
st.markdown('<div class="section-title">📁 ভিডিও আপলোড করুন</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "",
    type=["mp4", "avi", "mov", "mpeg4"],
    label_visibility="collapsed"
)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-title">🌍 ভাষা সিলেক্ট করুন</div>', unsafe_allow_html=True)
selected_langs = st.multiselect(
    "",
    list(LANGUAGES.keys()),
    default=["🇧🇩 বাংলা"],
    label_visibility="collapsed"
)

st.markdown("<br>", unsafe_allow_html=True)

# ---- TRANSLATE ----
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

# ---- BUTTON ----
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

        status.info("⏳ AI টেক্সট বের করছে...")
        model = whisper.load_model("base")
        result = model.transcribe("/tmp/audio.mp3", language="en")
        english_text = result["text"]
        progress.progress(40)

        step = 60 // len(selected_langs)
        current_progress = 40

        st.markdown("---")
        st.markdown('<div class="section-title">⬇️ ডাউনলোড করুন</div>', unsafe_allow_html=True)

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
                        label=f"⬇️ {lang_name} ভিডিও ডাউনলোড করুন",
                        data=f,
                        file_name=f"DubIT_{lang_code}.mp4",
                        mime="video/mp4",
                        key=lang_code
                    )

        progress.progress(100)
        status.empty()
        st.success("🎉 সব ডাবিং সম্পন্ন!")

# ---- FOOTER ----
st.markdown("""
<div class="footer">
    <div class="footer-brand">Made with Hasibur Joy by House IT LTD</div>
    <div class="footer-sub">DubIT — Bangladesh's First AI Video Dubbing Tool</div>
</div>
""", unsafe_allow_html=True)
