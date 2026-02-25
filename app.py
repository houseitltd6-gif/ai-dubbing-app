import streamlit as st
import subprocess, os, whisper, time
from gtts import gTTS
from googletrans import Translator

st.set_page_config(
    page_title="AI Video Dubbing",
    page_icon="🎬",
    layout="centered"
)

st.title("🎬 AI Video Dubbing Tool")
st.markdown("**ইংরেজি ভিডিও → ৫ ভাষায় ডাবিং**")
st.divider()

LANGUAGES = {
    "🇧🇩 বাংলা":   "bn",
    "🇮🇳 হিন্দি":  "hi",
    "🇵🇰 উর্দু":   "ur",
    "🇹🇷 টার্কিশ": "tr",
    "🇸🇦 আরবি":    "ar",
}

uploaded_file = st.file_uploader(
    "ইংরেজি ভিডিও আপলোড করুন",
    type=["mp4", "avi", "mov"]
)

selected_langs = st.multiselect(
    "কোন ভাষায় ডাব করতে চান?",
    list(LANGUAGES.keys()),
    default=["🇧🇩 বাংলা"]
)

def translate_text(text, lang_code):
    translator = Translator()
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
            time.sleep(0.5)
            r = translator.translate(chunk, src='en', dest=lang_code)
            if r and r.text:
                parts.append(r.text)
            else:
                parts.append(chunk)
        except:
            parts.append(chunk)
    return ' '.join(parts)

if st.button("🚀 ডাবিং শুরু করুন", type="primary"):
    if not uploaded_file:
        st.error("আগে ভিডিও আপলোড করুন!")
    elif not selected_langs:
        st.error("কমপক্ষে একটি ভাষা সিলেক্ট করুন!")
    else:
        # ভিডিও সেভ করা
        video_path = f"/tmp/input_video.mp4"
        with open(video_path, "wb") as f:
            f.write(uploaded_file.read())

        progress = st.progress(0)
        status = st.empty()

        # অডিও বের করা
        status.info("⏳ অডিও বের হচ্ছে...")
        subprocess.run(
            f'ffmpeg -i "{video_path}" -q:a 0 -map a /tmp/audio.mp3 -y',
            shell=True, capture_output=True
        )
        progress.progress(20)

        # ইংরেজি টেক্সট
        status.info("⏳ ইংরেজি টেক্সট বের হচ্ছে...")
        model = whisper.load_model("base")
        result = model.transcribe("/tmp/audio.mp3", language="en")
        english_text = result["text"]
        progress.progress(40)

        # প্রতিটি ভাষায় ডাবিং
        step = 60 // len(selected_langs)
        current_progress = 40

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

            # ডাউনলোড বাটন
            if os.path.exists(output_path):
                with open(output_path, "rb") as f:
                    st.download_button(
                        label=f"⬇️ {lang_name} ভিডিও ডাউনলোড করুন",
                        data=f,
                        file_name=f"dubbed_{lang_code}.mp4",
                        mime="video/mp4"
                    )

        progress.progress(100)
        status.success("🎉 সব ডাবিং সম্পন্ন!")

st.divider()
st.caption("Made with ❤️ | AI Video Dubbing Tool")
