import streamlit as st
import subprocess, os, whisper, asyncio
from gtts import gTTS
from deep_translator import GoogleTranslator
import edge_tts

# ---- ২০টি কণ্ঠ ----
ALL_VOICES = {
    # পুরুষ কণ্ঠ
    "👨 বাংলা পুরুষ (Pradeep)":     {"code": "bn-BD-PradeepNeural",    "lang": "bn"},
    "👨 ইংরেজি পুরুষ (Guy)":         {"code": "en-US-GuyNeural",         "lang": "en"},
    "👨 ইংরেজি পুরুষ (Davis)":       {"code": "en-US-DavisNeural",       "lang": "en"},
    "👨 ইংরেজি পুরুষ (Tony)":        {"code": "en-US-TonyNeural",        "lang": "en"},
    "👨 হিন্দি পুরুষ (Madhur)":      {"code": "hi-IN-MadhurNeural",      "lang": "hi"},
    "👨 উর্দু পুরুষ (Asad)":          {"code": "ur-PK-AsadNeural",        "lang": "ur"},
    "👨 টার্কিশ পুরুষ (Ahmet)":      {"code": "tr-TR-AhmetNeural",       "lang": "tr"},
    "👨 আরবি পুরুষ (Hamed)":         {"code": "ar-SA-HamedNeural",       "lang": "ar"},
    "👨 ফ্রেঞ্চ পুরুষ (Henri)":       {"code": "fr-FR-HenriNeural",       "lang": "fr"},
    "👨 জার্মান পুরুষ (Conrad)":      {"code": "de-DE-ConradNeural",      "lang": "de"},
    # মহিলা কণ্ঠ
    "👩 বাংলা মহিলা (Nabanita)":     {"code": "bn-BD-NabanitaNeural",    "lang": "bn"},
    "👩 ইংরেজি মহিলা (Jenny)":       {"code": "en-US-JennyNeural",       "lang": "en"},
    "👩 ইংরেজি মহিলা (Aria)":        {"code": "en-US-AriaNeural",        "lang": "en"},
    "👩 ইংরেজি মহিলা (Sara)":        {"code": "en-US-SaraNeural",        "lang": "en"},
    "👩 হিন্দি মহিলা (Swara)":       {"code": "hi-IN-SwaraNeural",       "lang": "hi"},
    "👩 উর্দু মহিলা (Uzma)":          {"code": "ur-PK-UzmaNeural",        "lang": "ur"},
    "👩 টার্কিশ মহিলা (Emel)":       {"code": "tr-TR-EmelNeural",        "lang": "tr"},
    "👩 আরবি মহিলা (Zariyah)":       {"code": "ar-SA-ZariyahNeural",     "lang": "ar"},
    "👩 ফ্রেঞ্চ মহিলা (Denise)":      {"code": "fr-FR-DeniseNeural",      "lang": "fr"},
    "👩 জার্মান মহিলা (Katja)":       {"code": "de-DE-KatjaNeural",       "lang": "de"},
}

SOURCE_LANGUAGES = {
    "🇧🇩 বাংলা":   "bn",
    "🇺🇸 ইংরেজি": "en",
    "🇮🇳 হিন্দি":  "hi",
    "🇵🇰 উর্দু":   "ur",
    "🇹🇷 টার্কিশ": "tr",
    "🇸🇦 আরবি":    "ar",
}

TARGET_LANGUAGES = {
    "🇧🇩 বাংলা":   "bn",
    "🇺🇸 ইংরেজি": "en",
    "🇮🇳 হিন্দি":  "hi",
    "🇵🇰 উর্দু":   "ur",
    "🇹🇷 টার্কিশ": "tr",
    "🇸🇦 আরবি":    "ar",
}

st.set_page_config(
    page_title="DubIT — AI Video Dubbing",
    page_icon="🎬",
    layout="centered"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp { background: #080812; }
.hero {
    background: linear-gradient(135deg, #1a0533 0%, #0d1b4b 50%, #001a3a 100%);
    border: 1px solid rgba(139, 92, 246, 0.3);
    border-radius: 24px;
    padding: 3rem 2rem;
    text-align: center;
    margin-bottom: 2rem;
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
}
.hero p { color: #94a3b8; font-size: 1.1rem; margin: 0; }
.stats-row { display: flex; gap: 1rem; margin-bottom: 2rem; }
.stat-card {
    flex: 1;
    background: linear-gradient(135deg, #0f0f1f, #1a1a35);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 16px;
    padding: 1.2rem;
    text-align: center;
}
.stat-number {
    font-size: 1.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.stat-label { color: #64748b; font-size: 0.8rem; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; }
.section-title {
    color: #e2e8f0;
    font-size: 1rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 0.8rem;
}
.stFileUploader > div {
    background: linear-gradient(135deg, #0f0f1f, #1a1a35) !important;
    border: 2px dashed rgba(139, 92, 246, 0.4) !important;
    border-radius: 16px !important;
}
.stMultiSelect > div > div {
    background: #0f0f1f !important;
    border: 1px solid rgba(139, 92, 246, 0.3) !important;
    border-radius: 12px !important;
}
.stSelectbox > div > div {
    background: #0f0f1f !important;
    border: 1px solid rgba(139, 92, 246, 0.3) !important;
    border-radius: 12px !important;
}
.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #2563eb) !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 1rem 2rem !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    width: 100% !important;
    box-shadow: 0 4px 20px rgba(124, 58, 237, 0.4) !important;
}
.stProgress > div > div {
    background: linear-gradient(135deg, #7c3aed, #2563eb) !important;
    border-radius: 10px !important;
}
.stDownloadButton > button {
    background: linear-gradient(135deg, #065f46, #047857) !important;
    color: white !important;
    border: 1px solid rgba(16, 185, 129, 0.3) !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    width: 100% !important;
    margin-bottom: 0.5rem !important;
}
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
.footer-sub { color: #334155; font-size: 0.8rem; margin-top: 0.3rem; }
footer { visibility: hidden; }
#MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ---- SESSION STATE ----
if "dubbed_files" not in st.session_state:
    st.session_state.dubbed_files = {}
if "dubbing_done" not in st.session_state:
    st.session_state.dubbing_done = False
if "selected_voice_key" not in st.session_state:
    st.session_state.selected_voice_key = ""

# ---- HERO ----
st.markdown("""
<div class="hero">
    <div class="hero-badge">🇧🇩 Bangladesh's First</div>
    <h1>DubIT</h1>
    <p>যেকোনো ভিডিও → ৬ ভাষায় AI ডাবিং | সম্পূর্ণ ফ্রি</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="stats-row">
    <div class="stat-card"><div class="stat-number">6+</div><div class="stat-label">ভাষা</div></div>
    <div class="stat-card"><div class="stat-number">20</div><div class="stat-label">কণ্ঠ</div></div>
    <div class="stat-card"><div class="stat-number">FREE</div><div class="stat-label">সম্পূর্ণ ফ্রি</div></div>
    <div class="stat-card"><div class="stat-number">200MB</div><div class="stat-label">ফাইল লিমিট</div></div>
</div>
""", unsafe_allow_html=True)


# ---- FUNCTIONS ----
async def tts_async(text, voice_name, output_path):
    communicate = edge_tts.Communicate(text, voice_name)
    await communicate.save(output_path)

def text_to_speech(text, voice_code, output_path):
    try:
        asyncio.run(tts_async(text, voice_code, output_path))
        return True
    except:
        return False

def text_to_speech_gtts(text, lang_code, output_path):
    try:
        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save(output_path)
        return True
    except:
        return False

def translate_text(text, src_code, dest_code):
    if src_code == dest_code:
        return text
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
            translated = GoogleTranslator(source=src_code, target=dest_code).translate(chunk)
            parts.append(translated if translated else chunk)
        except:
            parts.append(chunk)
    return ' '.join(parts)


# ---- DOWNLOAD PAGE ----
if st.session_state.dubbing_done and st.session_state.dubbed_files:
    st.success("🎉 ডাবিং সম্পন্ন!")
    st.info(f"🎙️ ব্যবহৃত কণ্ঠ: {st.session_state.selected_voice_key}")
    st.markdown('<div class="section-title">⬇️ ডাউনলোড করুন</div>', unsafe_allow_html=True)

    for lang_name, data in st.session_state.dubbed_files.items():
        st.download_button(
            label=f"⬇️ {lang_name} ভিডিও ডাউনলোড করুন",
            data=data["bytes"],
            file_name=data["filename"],
            mime="video/mp4",
            key=f"dl_{lang_name}"
        )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 নতুন ভিডিও ডাব করুন"):
        st.session_state.dubbed_files = {}
        st.session_state.dubbing_done = False
        st.rerun()

# ---- MAIN PAGE ----
else:
    st.markdown('<div class="section-title">📁 ভিডিও আপলোড করুন</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "",
        type=["mp4", "avi", "mov", "mpeg4"],
        label_visibility="collapsed"
    )

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">📥 মূল ভাষা</div>', unsafe_allow_html=True)
        source_lang = st.selectbox(
            "",
            list(SOURCE_LANGUAGES.keys()),
            index=1,
            label_visibility="collapsed",
            key="src_lang"
        )
    with col2:
        st.markdown('<div class="section-title">📤 টার্গেট ভাষা</div>', unsafe_allow_html=True)
        target_options = [l for l in TARGET_LANGUAGES.keys() if l != source_lang]
        selected_langs = st.multiselect(
            "",
            target_options,
            default=[target_options[0]] if target_options else [],
            label_visibility="collapsed"
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">🎙️ কণ্ঠ বেছে নিন (২০টি অপশন)</div>', unsafe_allow_html=True)

    voice_names = list(ALL_VOICES.keys())
    male_voices = [v for v in voice_names if "👨" in v]
    female_voices = [v for v in voice_names if "👩" in v]

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("**👨 পুরুষ কণ্ঠ**")
        selected_male = st.selectbox(
            "",
            ["-- বেছে নিন --"] + male_voices,
            label_visibility="collapsed",
            key="male_voice"
        )
    with col4:
        st.markdown("**👩 মহিলা কণ্ঠ**")
        selected_female = st.selectbox(
            "",
            ["-- বেছে নিন --"] + female_voices,
            label_visibility="collapsed",
            key="female_voice"
        )

    # কোন কণ্ঠ selected তা নির্ধারণ
    if selected_male != "-- বেছে নিন --":
        final_voice = selected_male
    elif selected_female != "-- বেছে নিন --":
        final_voice = selected_female
    else:
        final_voice = "👨 ইংরেজি পুরুষ (Guy)"

    st.info(f"✅ নির্বাচিত কণ্ঠ: **{final_voice}**")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 ডাবিং শুরু করুন"):
        if not uploaded_file:
            st.error("⚠️ আগে ভিডিও আপলোড করুন!")
        elif not selected_langs:
            st.error("⚠️ কমপক্ষে একটি টার্গেট ভাষা সিলেক্ট করুন!")
        else:
            voice_code = ALL_VOICES[final_voice]["code"]
            src_code = SOURCE_LANGUAGES[source_lang]

            video_path = "/tmp/input_video.mp4"
            with open(video_path, "wb") as f:
                f.write(uploaded_file.read())

            progress = st.progress(0)
            status = st.empty()

            status.info("⏳ অডিও বের হচ্ছে...")
            subprocess.run(
                f'ffmpeg -i "{video_path}" -q:a 0 -map a /tmp/audio_src.mp3 -y',
                shell=True, capture_output=True
            )
            progress.progress(20)

            status.info("⏳ AI টেক্সট বের করছে...")
            model = whisper.load_model("base")
            result = model.transcribe("/tmp/audio_src.mp3", language=src_code)
            source_text = result["text"]
            progress.progress(40)

            step = 60 // len(selected_langs)
            current_progress = 40
            dubbed_files = {}

            for lang_name in selected_langs:
                dest_code = TARGET_LANGUAGES[lang_name]
                status.info(f"⏳ {lang_name} — {final_voice} দিয়ে ডাবিং হচ্ছে...")

                translated = translate_text(source_text, src_code, dest_code)
                audio_path = f"/tmp/audio_{dest_code}.mp3"

                success = text_to_speech(translated, voice_code, audio_path)
                if not success:
                    text_to_speech_gtts(translated, dest_code, audio_path)

                output_path = f"/tmp/dubbed_{dest_code}.mp4"
                subprocess.run(
                    f'ffmpeg -i "{video_path}" -i "{audio_path}" '
                    f'-c:v copy -map 0:v:0 -map 1:a:0 -shortest "{output_path}" -y',
                    shell=True, capture_output=True
                )

                current_progress += step
                progress.progress(min(current_progress, 100))

                if os.path.exists(output_path):
                    with open(output_path, "rb") as f:
                        file_bytes = f.read()
                    dubbed_files[lang_name] = {
                        "bytes": file_bytes,
                        "filename": f"DubIT_{dest_code}.mp4"
                    }

            progress.progress(100)
            status.empty()
            st.session_state.dubbed_files = dubbed_files
            st.session_state.dubbing_done = True
            st.session_state.selected_voice_key = final_voice
            st.rerun()

# ---- FOOTER ----
st.markdown("""
<div class="footer">
    <div class="footer-brand">Made with Hasibur Joy by House IT LTD</div>
    <div class="footer-sub">DubIT — Bangladesh's First AI Video Dubbing Tool</div>
</div>
""", unsafe_allow_html=True)
