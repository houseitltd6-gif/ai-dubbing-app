import streamlit as st
import subprocess, os, whisper
from gtts import gTTS
from deep_translator import GoogleTranslator

ALL_VOICES = {
    "👨 বাংলা পুরুষ — Pradeep":    "bn-BD-PradeepNeural",
    "👩 বাংলা মহিলা — Nabanita":   "bn-BD-NabanitaNeural",
    "👨 ইংরেজি পুরুষ — Guy":        "en-US-GuyNeural",
    "👨 ইংরেজি পুরুষ — Davis":      "en-US-DavisNeural",
    "👨 ইংরেজি পুরুষ — Tony":       "en-US-TonyNeural",
    "👩 ইংরেজি মহিলা — Jenny":      "en-US-JennyNeural",
    "👩 ইংরেজি মহিলা — Aria":       "en-US-AriaNeural",
    "👩 ইংরেজি মহিলা — Sara":       "en-US-SaraNeural",
    "👨 হিন্দি পুরুষ — Madhur":     "hi-IN-MadhurNeural",
    "👩 হিন্দি মহিলা — Swara":      "hi-IN-SwaraNeural",
    "👨 উর্দু পুরুষ — Asad":         "ur-PK-AsadNeural",
    "👩 উর্দু মহিলা — Uzma":         "ur-PK-UzmaNeural",
    "👨 টার্কিশ পুরুষ — Ahmet":     "tr-TR-AhmetNeural",
    "👩 টার্কিশ মহিলা — Emel":      "tr-TR-EmelNeural",
    "👨 আরবি পুরুষ — Hamed":        "ar-SA-HamedNeural",
    "👩 আরবি মহিলা — Zariyah":      "ar-SA-ZariyahNeural",
    "👨 ফ্রেঞ্চ পুরুষ — Henri":      "fr-FR-HenriNeural",
    "👩 ফ্রেঞ্চ মহিলা — Denise":     "fr-FR-DeniseNeural",
    "👨 জার্মান পুরুষ — Conrad":     "de-DE-ConradNeural",
    "👩 জার্মান মহিলা — Katja":      "de-DE-KatjaNeural",
}

PREVIEW_TEXT = {
    "bn": "হ্যালো, আমি DubIT এর কণ্ঠ।",
    "en": "Hello, I am a DubIT voice.",
    "hi": "नमस्ते, मैं DubIT की आवाज़ हूँ।",
    "ur": "ہیلو، میں DubIT کی آواز ہوں۔",
    "tr": "Merhaba, ben DubIT sesinim.",
    "ar": "مرحبا، أنا صوت DubIT.",
    "fr": "Bonjour, je suis la voix DubIT.",
    "de": "Hallo, ich bin die DubIT Stimme.",
}

LANG_DEFAULT_VOICE = {
    "bn": "bn-BD-PradeepNeural",
    "en": "en-US-GuyNeural",
    "hi": "hi-IN-MadhurNeural",
    "ur": "ur-PK-AsadNeural",
    "tr": "tr-TR-AhmetNeural",
    "ar": "ar-SA-HamedNeural",
    "fr": "fr-FR-HenriNeural",
    "de": "de-DE-ConradNeural",
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

# ---- FUNCTIONS ----
def text_to_speech(text, voice_code, output_path):
    try:
        text_file = "/tmp/tts_input.txt"
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(text)
        result = subprocess.run(
            f'edge-tts --voice "{voice_code}" --file "{text_file}" --write-media "{output_path}"',
            shell=True, capture_output=True, text=True, timeout=60
        )
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
        return False
    except:
        return False

def text_to_speech_gtts(text, lang_code, output_path):
    try:
        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save(output_path)
        return True
    except:
        return False

def get_duration(path):
    result = subprocess.run(
        f'ffprobe -v error -show_entries format=duration '
        f'-of default=noprint_wrappers=1:nokey=1 "{path}"',
        shell=True, capture_output=True, text=True
    )
    try:
        return float(result.stdout.strip())
    except:
        return 0

def get_compatible_voice(selected_voice_code, dest_lang_code):
    voice_lang = selected_voice_code[:2]
    if voice_lang == dest_lang_code:
        return selected_voice_code
    return LANG_DEFAULT_VOICE.get(dest_lang_code, "en-US-GuyNeural")

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
    st.markdown('<div class="section-title">🎙️ কণ্ঠ বেছে নিন ও শুনুন</div>', unsafe_allow_html=True)

    selected_voice = st.selectbox(
        "",
        list(ALL_VOICES.keys()),
        label_visibility="collapsed",
        key="voice_select"
    )

    col_prev, col_space = st.columns([1, 2])
    with col_prev:
        if st.button("🔊 এই কণ্ঠ শুনুন"):
            voice_code = ALL_VOICES[selected_voice]
            lang_code = voice_code[:2]
            preview_text = PREVIEW_TEXT.get(lang_code, PREVIEW_TEXT["en"])
            preview_path = "/tmp/preview_voice.mp3"
            with st.spinner("কণ্ঠ তৈরি হচ্ছে..."):
                success = text_to_speech(preview_text, voice_code, preview_path)
                if success:
                    with open(preview_path, "rb") as f:
                        st.audio(f.read(), format="audio/mp3")
                else:
                    st.warning("Preview তৈরি করা যায়নি।")

    st.info(f"✅ নির্বাচিত কণ্ঠ: **{selected_voice}**")
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 ডাবিং শুরু করুন"):
        if not uploaded_file:
            st.error("⚠️ আগে ভিডিও আপলোড করুন!")
        elif not selected_langs:
            st.error("⚠️ কমপক্ষে একটি টার্গেট ভাষা সিলেক্ট করুন!")
        else:
            voice_code = ALL_VOICES[selected_voice]
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

            video_duration = get_duration(video_path)
            step = 60 // len(selected_langs)
            current_progress = 40
            dubbed_files = {}

            for lang_name in selected_langs:
                dest_code = TARGET_LANGUAGES[lang_name]
                status.info(f"⏳ {lang_name} ডাবিং হচ্ছে...")

                translated = translate_text(source_text, src_code, dest_code)
                audio_path = f"/tmp/audio_{dest_code}.mp3"

                compatible_voice = get_compatible_voice(voice_code, dest_code)
                success = text_to_speech(translated, compatible_voice, audio_path)
                if not success:
                    text_to_speech_gtts(translated, dest_code, audio_path)

                padded_audio = f"/tmp/audio_padded_{dest_code}.mp3"
                audio_duration = get_duration(audio_path)

                if audio_duration > 0 and audio_duration < video_duration:
                    subprocess.run(
                        f'ffmpeg -i "{audio_path}" '
                        f'-af "apad=pad_dur={video_duration - audio_duration}" '
                        f'-t {video_duration} "{padded_audio}" -y',
                        shell=True, capture_output=True
                    )
                else:
                    padded_audio = audio_path

                output_path = f"/tmp/dubbed_{dest_code}.mp4"
                subprocess.run(
                    f'ffmpeg -i "{video_path}" -i "{padded_audio}" '
                    f'-c:v copy -map 0:v:0 -map 1:a:0 '
                    f'-t {video_duration} "{output_path}" -y',
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
            st.session_state.selected_voice_key = selected_voice
            st.rerun()

# ---- FOOTER ----
st.markdown("""
<div class="footer">
    <div class="footer-brand">Made with Hasibur Joy by House IT LTD</div>
    <div class="footer-sub">DubIT — Bangladesh's First AI Video Dubbing Tool</div>
</div>
""", unsafe_allow_html=True)
```

**requirements.txt থেকে `nest_asyncio` এবং `elevenlabs` মুছে দিন। শুধু এটা রাখুন:**
```
openai-whisper
gtts
deep-translator
streamlit
ffmpeg-python
edge-tts
