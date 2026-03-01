import streamlit as st
import subprocess, os, whisper, json, uuid
from datetime import datetime, date
from gtts import gTTS
from deep_translator import GoogleTranslator, MyMemoryTranslator

ALL_VOICES = {
    "👨 বাংলা পুরুষ — Pradeep":     "bn-BD-PradeepNeural",
    "👩 বাংলা মহিলা — Nabanita":    "bn-BD-NabanitaNeural",
    "👨 ইংরেজি পুরুষ — Guy":         "en-US-GuyNeural",
    "👨 ইংরেজি পুরুষ — Christopher": "en-US-ChristopherNeural",
    "👨 ইংরেজি পুরুষ — Eric":        "en-US-EricNeural",
    "👩 ইংরেজি মহিলা — Jenny":       "en-US-JennyNeural",
    "👩 ইংরেজি মহিলা — Aria":        "en-US-AriaNeural",
    "👩 ইংরেজি মহিলা — Sara":        "en-US-SaraNeural",
    "👨 হিন্দি পুরুষ — Madhur":      "hi-IN-MadhurNeural",
    "👩 হিন্দি মহিলা — Swara":       "hi-IN-SwaraNeural",
    "👨 উর্দু পুরুষ — Asad":          "ur-PK-AsadNeural",
    "👩 উর্দু মহিলা — Uzma":          "ur-PK-UzmaNeural",
    "👨 টার্কিশ পুরুষ — Ahmet":      "tr-TR-AhmetNeural",
    "👩 টার্কিশ মহিলা — Emel":       "tr-TR-EmelNeural",
    "👨 আরবি পুরুষ — Hamed":         "ar-SA-HamedNeural",
    "👩 আরবি মহিলা — Zariyah":       "ar-SA-ZariyahNeural",
    "👨 ফ্রেঞ্চ পুরুষ — Henri":       "fr-FR-HenriNeural",
    "👩 ফ্রেঞ্চ মহিলা — Denise":      "fr-FR-DeniseNeural",
    "👨 জার্মান পুরুষ — Conrad":      "de-DE-ConradNeural",
    "👩 জার্মান মহিলা — Katja":       "de-DE-KatjaNeural",
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

BKASH_NUMBER  = "01821282411"
ADMIN_USER    = "hasibur@dubit.com"
ADMIN_PASS    = "dubit2024admin"
FREE_LIMIT    = 3
PREMIUM_FILE  = "/tmp/premium_users.json"
USAGE_FILE    = "/tmp/usage_tracker.json"
USERS_FILE    = "/tmp/registered_users.json"

# ---- HELPERS ----
def load_json(path):
    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
    except:
        pass
    return {}

def save_json(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f)
    except:
        pass

def is_premium(uid):
    return load_json(PREMIUM_FILE).get(uid, {}).get("active", False)

def get_usage(uid):
    return load_json(USAGE_FILE).get(uid, {}).get(str(date.today()), 0)

def inc_usage(uid):
    data = load_json(USAGE_FILE)
    today = str(date.today())
    if uid not in data:
        data[uid] = {}
    data[uid][today] = data[uid].get(today, 0) + 1
    save_json(USAGE_FILE, data)

def register_user(email, password):
    data = load_json(USERS_FILE)
    if email in data:
        return False, "এই email আগেই registered!"
    data[email] = {
        "password": password,
        "uid": str(uuid.uuid4())[:8],
        "joined": str(datetime.now())[:16]
    }
    save_json(USERS_FILE, data)
    return True, data[email]["uid"]

def login_user(email, password):
    data = load_json(USERS_FILE)
    if email not in data:
        return False, "Email পাওয়া যায়নি!"
    if data[email]["password"] != password:
        return False, "Password ভুল!"
    return True, data[email]["uid"]

# ---- PAGE CONFIG ----
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
.auth-box {
    background: linear-gradient(135deg, #0f0f1f, #1a1a35);
    border: 1px solid rgba(139, 92, 246, 0.3);
    border-radius: 20px;
    padding: 2rem;
    margin: 1rem 0;
}
.premium-box {
    background: linear-gradient(135deg, #1a0533, #0d1b4b);
    border: 2px solid rgba(139, 92, 246, 0.5);
    border-radius: 20px;
    padding: 2rem;
    text-align: center;
    margin: 1rem 0;
}
.free-box {
    background: linear-gradient(135deg, #0f0f1f, #1a1a35);
    border: 1px solid rgba(100, 116, 139, 0.3);
    border-radius: 20px;
    padding: 2rem;
    text-align: center;
    margin: 1rem 0;
}
.plan-price {
    font-size: 2.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.badge-premium {
    display: inline-block;
    background: linear-gradient(135deg, #7c3aed, #2563eb);
    color: white;
    padding: 0.3rem 1rem;
    border-radius: 50px;
    font-size: 0.8rem;
    font-weight: 700;
}
.badge-free {
    display: inline-block;
    background: rgba(100, 116, 139, 0.3);
    color: #94a3b8;
    padding: 0.3rem 1rem;
    border-radius: 50px;
    font-size: 0.8rem;
    font-weight: 700;
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
.stTextInput > div > div {
    background: #0f0f1f !important;
    border: 1px solid rgba(139, 92, 246, 0.3) !important;
    border-radius: 12px !important;
    color: white !important;
}
.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #2563eb) !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 1rem 2rem !important;
    font-size: 1rem !important;
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
if "dubbed_files"    not in st.session_state: st.session_state.dubbed_files    = {}
if "dubbing_done"    not in st.session_state: st.session_state.dubbing_done    = False
if "selected_voice"  not in st.session_state: st.session_state.selected_voice  = ""
if "page"            not in st.session_state: st.session_state.page            = "login"
if "user_email"      not in st.session_state: st.session_state.user_email      = ""
if "user_uid"        not in st.session_state: st.session_state.user_uid        = ""
if "is_admin"        not in st.session_state: st.session_state.is_admin        = False

# ---- FUNCTIONS ----
def text_to_speech(text, voice_code, output_path):
    try:
        text_file = "/tmp/tts_input.txt"
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(text)
        subprocess.run(
            f'edge-tts --voice "{voice_code}" --file "{text_file}" --write-media "{output_path}"',
            shell=True, capture_output=True, timeout=120
        )
        return os.path.exists(output_path) and os.path.getsize(output_path) > 1000
    except:
        return False

def text_to_speech_gtts(text, lang_code, output_path):
    try:
        lang = lang_code if lang_code in ["bn","hi","ur","tr","ar","fr","de"] else "en"
        gTTS(text=text, lang=lang, slow=False).save(output_path)
        return os.path.exists(output_path) and os.path.getsize(output_path) > 1000
    except:
        return False

def get_duration(path):
    r = subprocess.run(
        f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{path}"',
        shell=True, capture_output=True, text=True
    )
    try:
        return float(r.stdout.strip())
    except:
        return 0

def get_compatible_voice(voice_code, dest_lang):
    if voice_code[:2] == dest_lang:
        return voice_code
    return LANG_DEFAULT_VOICE.get(dest_lang, "en-US-GuyNeural")

def translate_text(text, src, dest):
    if src == dest:
        return text
    sentences = text.split('. ')
    chunks, cur = [], ""
    for s in sentences:
        if len(cur) + len(s) < 400:
            cur += s + ". "
        else:
            chunks.append(cur)
            cur = s + ". "
    if cur:
        chunks.append(cur)
    parts = []
    for chunk in chunks:
        if not chunk.strip():
            continue
        try:
            t = MyMemoryTranslator(source=src, target=dest).translate(chunk.strip())
            parts.append(t if t and len(t) > 2 else chunk)
        except:
            try:
                t = GoogleTranslator(source=src, target=dest).translate(chunk.strip())
                parts.append(t if t else chunk)
            except:
                parts.append(chunk)
    return ' '.join(parts)

# ==================================================
# ADMIN PANEL — আলাদা পেজ
# ==================================================
query_params = st.query_params
is_admin_url = query_params.get("panel", "") == "dubitadmin2024"

if is_admin_url or st.session_state.is_admin:
    # Admin login
    if not st.session_state.is_admin:
        st.markdown("""
        <div class="hero">
            <h1>🔑 Admin</h1>
            <p>DubIT Admin Panel</p>
        </div>
        """, unsafe_allow_html=True)
        a_user = st.text_input("Admin Email", placeholder="admin email")
        a_pass = st.text_input("Password", type="password", placeholder="password")
        if st.button("🔑 Login"):
            if a_user == ADMIN_USER and a_pass == ADMIN_PASS:
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("❌ Wrong credentials!")
    else:
        # Admin dashboard
        st.markdown("""
        <div class="hero">
            <h1>🔑 Admin Panel</h1>
            <p>DubIT Management Dashboard</p>
        </div>
        """, unsafe_allow_html=True)

        col_stat1, col_stat2, col_stat3 = st.columns(3)
        all_premium = load_json(PREMIUM_FILE)
        all_users   = load_json(USERS_FILE)
        pending     = {k:v for k,v in all_premium.items() if not v.get("active", False)}
        active      = {k:v for k,v in all_premium.items() if v.get("active", False)}

        with col_stat1:
            st.metric("👥 Total Users", len(all_users))
        with col_stat2:
            st.metric("⭐ Premium", len(active))
        with col_stat3:
            st.metric("⏳ Pending", len(pending))

        st.markdown("---")

        # Pending requests
        if pending:
            st.markdown("### ⏳ Pending Payment Requests")
            for uid, info in pending.items():
                with st.container():
                    st.markdown(f"""
                    **UID:** `{uid}` | **TXN:** `{info.get('txn_id')}` | **Date:** {info.get('date','')[:16]}
                    """)
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(f"✅ Approve", key=f"ap_{uid}"):
                            all_premium[uid]["active"] = True
                            save_json(PREMIUM_FILE, all_premium)
                            st.success("Approved!")
                            st.rerun()
                    with c2:
                        if st.button(f"❌ Reject", key=f"rj_{uid}"):
                            del all_premium[uid]
                            save_json(PREMIUM_FILE, all_premium)
                            st.warning("Rejected!")
                            st.rerun()
                    st.markdown("---")
        else:
            st.info("কোনো pending request নেই।")

        # Active premium users
        if active:
            st.markdown("### ⭐ Active Premium Users")
            for uid, info in active.items():
                st.markdown(f"✅ `{uid}` — TXN: `{info.get('txn_id')}` — {info.get('date','')[:16]}")

        # Registered users
        if all_users:
            st.markdown("### 👥 Registered Users")
            for email, info in all_users.items():
                premium_status = "⭐" if is_premium(info.get("uid","")) else "🆓"
                usage = get_usage(info.get("uid",""))
                st.markdown(f"{premium_status} `{email}` — UID: `{info.get('uid')}` — আজ: {usage} ভিডিও")

        st.markdown("---")
        if st.button("🚪 Admin Logout"):
            st.session_state.is_admin = False
            st.rerun()

    st.stop()

# ==================================================
# USER PANEL
# ==================================================

# ---- HERO ----
st.markdown("""
<div class="hero">
    <div class="hero-badge">🇧🇩 Bangladesh's First</div>
    <h1>DubIT</h1>
    <p>যেকোনো ভিডিও → ৬ ভাষায় AI ডাবিং</p>
</div>
""", unsafe_allow_html=True)

# ---- LOGIN / REGISTER ----
if not st.session_state.user_uid:
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

    with tab1:
        st.markdown('<div class="auth-box">', unsafe_allow_html=True)
        st.markdown("### 🔐 Login করুন")
        l_email = st.text_input("Email", placeholder="আপনার email দিন", key="l_email")
        l_pass  = st.text_input("Password", type="password", placeholder="password", key="l_pass")
        if st.button("🚀 Login"):
            if not l_email or not l_pass:
                st.error("Email ও Password দিন!")
            else:
                ok, result = login_user(l_email, l_pass)
                if ok:
                    st.session_state.user_email = l_email
                    st.session_state.user_uid   = result
                    st.session_state.page       = "main"
                    st.rerun()
                else:
                    st.error(f"❌ {result}")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="auth-box">', unsafe_allow_html=True)
        st.markdown("### 📝 নতুন Account বানান")
        r_email = st.text_input("Email", placeholder="আপনার email দিন", key="r_email")
        r_pass  = st.text_input("Password", type="password", placeholder="কমপক্ষে ৬ অক্ষর", key="r_pass")
        r_pass2 = st.text_input("Confirm Password", type="password", placeholder="আবার দিন", key="r_pass2")
        if st.button("✅ Register"):
            if not r_email or not r_pass:
                st.error("সব field পূরণ করুন!")
            elif len(r_pass) < 6:
                st.error("Password কমপক্ষে ৬ অক্ষর হতে হবে!")
            elif r_pass != r_pass2:
                st.error("Password match করছে না!")
            elif "@" not in r_email:
                st.error("সঠিক email দিন!")
            else:
                ok, result = register_user(r_email, r_pass)
                if ok:
                    st.success("✅ Registration সফল! এখন login করুন।")
                else:
                    st.error(f"❌ {result}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()

# ---- LOGGED IN USER ----
uid           = st.session_state.user_uid
user_premium  = is_premium(uid)
today_usage   = get_usage(uid)
remaining     = max(0, FREE_LIMIT - today_usage)

# Stats
if user_premium:
    st.markdown("""
    <div class="stats-row">
        <div class="stat-card"><div class="stat-number">6+</div><div class="stat-label">ভাষা</div></div>
        <div class="stat-card"><div class="stat-number">20</div><div class="stat-label">কণ্ঠ</div></div>
        <div class="stat-card"><div class="stat-number">∞</div><div class="stat-label">Unlimited</div></div>
        <div class="stat-card"><div class="stat-number">⭐</div><div class="stat-label">Premium</div></div>
    </div>
    """, unsafe_allow_html=True)
    st.success(f"⭐ Premium Member | {st.session_state.user_email}")
else:
    st.markdown(f"""
    <div class="stats-row">
        <div class="stat-card"><div class="stat-number">6+</div><div class="stat-label">ভাষা</div></div>
        <div class="stat-card"><div class="stat-number">20</div><div class="stat-label">কণ্ঠ</div></div>
        <div class="stat-card"><div class="stat-number">FREE</div><div class="stat-label">ফ্রি</div></div>
        <div class="stat-card"><div class="stat-number">{remaining}/3</div><div class="stat-label">আজকের বাকি</div></div>
    </div>
    """, unsafe_allow_html=True)

# Nav
col_n1, col_n2, col_n3 = st.columns(3)
with col_n1:
    if st.button("🎬 ডাবিং"):
        st.session_state.page = "main"
        st.session_state.dubbing_done = False
        st.rerun()
with col_n2:
    if st.button("⭐ Premium"):
        st.session_state.page = "premium"
        st.rerun()
with col_n3:
    if st.button("🚪 Logout"):
        st.session_state.user_email = ""
        st.session_state.user_uid   = ""
        st.session_state.page       = "login"
        st.session_state.dubbing_done = False
        st.rerun()

st.markdown("---")

# ============================
# PREMIUM PAGE
# ============================
if st.session_state.page == "premium":
    if user_premium:
        st.success("⭐ আপনি ইতিমধ্যে Premium Member!")
    else:
        st.markdown('<div class="section-title">⭐ Premium Plan</div>', unsafe_allow_html=True)

        col_f, col_p = st.columns(2)
        with col_f:
            st.markdown("""
            <div class="free-box">
                <div class="badge-free">FREE</div>
                <div class="plan-price">৳০</div>
                <p style="color:#94a3b8">প্রতি মাসে</p>
                <hr style="border-color:rgba(255,255,255,0.1)">
                <p style="color:#94a3b8;font-size:0.9rem">
                ✅ ৩টি ভিডিও/দিন<br>
                ✅ ৬ ভাষা<br>
                ✅ ২০টি কণ্ঠ<br>
                ❌ Limited
                </p>
            </div>
            """, unsafe_allow_html=True)
        with col_p:
            st.markdown("""
            <div class="premium-box">
                <div class="badge-premium">PREMIUM ⭐</div>
                <div class="plan-price">৳৯৯</div>
                <p style="color:#a78bfa">প্রতি মাসে</p>
                <hr style="border-color:rgba(139,92,246,0.3)">
                <p style="color:#e2e8f0;font-size:0.9rem">
                ✅ Unlimited ভিডিও<br>
                ✅ ৬ ভাষা<br>
                ✅ ২০টি কণ্ঠ<br>
                ✅ Priority processing
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0f0f1f,#1a1a35);border:1px solid
        rgba(139,92,246,0.3);border-radius:16px;padding:1.5rem;text-align:center;margin:1rem 0">
            <h3 style="color:#a78bfa">📱 bKash এ পেমেন্ট করুন</h3>
            <p style="color:#94a3b8">Send Money করুন:</p>
            <h2 style="color:white;font-size:2rem;letter-spacing:3px">{BKASH_NUMBER}</h2>
            <p style="color:#a78bfa;font-weight:700">Amount: ৯৯ টাকা</p>
            <p style="color:#64748b;font-size:0.85rem">bKash → Send Money → নম্বর দিন → ৯৯ টাকা</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-title">📋 Transaction ID দিন</div>', unsafe_allow_html=True)
        txn_id = st.text_input("", placeholder="যেমন: 8A3B9F2K1M", label_visibility="collapsed")

        if st.button("✅ Premium Activate করুন"):
            if not txn_id or len(txn_id) < 5:
                st.error("⚠️ সঠিক Transaction ID দিন!")
            else:
                all_p = load_json(PREMIUM_FILE)
                all_txns = [v.get("txn_id") for v in all_p.values()]
                if txn_id in all_txns:
                    st.error("⚠️ এই Transaction ID আগেই ব্যবহার হয়েছে!")
                else:
                    all_p[uid] = {
                        "active": False,
                        "txn_id": txn_id,
                        "email": st.session_state.user_email,
                        "date": str(datetime.now())[:16],
                        "status": "pending"
                    }
                    save_json(PREMIUM_FILE, all_p)
                    st.success("✅ Request পাঠানো হয়েছে! Admin verify করলে Premium activate হবে।")

# ============================
# DOWNLOAD PAGE
# ============================
elif st.session_state.dubbing_done and st.session_state.dubbed_files:
    st.success("🎉 ডাবিং সম্পন্ন!")
    st.info(f"🎙️ কণ্ঠ: {st.session_state.selected_voice}")
    st.markdown('<div class="section-title">⬇️ ডাউনলোড করুন</div>', unsafe_allow_html=True)

    for lang_name, data in st.session_state.dubbed_files.items():
        st.download_button(
            label=f"⬇️ {lang_name} ভিডিও ডাউনলোড করুন",
            data=data["bytes"],
            file_name=data["filename"],
            mime="video/mp4",
            key=f"dl_{lang_name}"
        )

    if st.button("🔄 নতুন ভিডিও ডাব করুন"):
        st.session_state.dubbed_files = {}
        st.session_state.dubbing_done = False
        st.session_state.page = "main"
        st.rerun()

# ============================
# MAIN DUBBING PAGE
# ============================
else:
    if not user_premium and today_usage >= FREE_LIMIT:
        st.error("⚠️ আজকের ফ্রি limit শেষ!")
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1a0533,#0d1b4b);border:2px solid
        rgba(139,92,246,0.5);border-radius:20px;padding:2rem;text-align:center">
            <h3 style="color:#a78bfa">⭐ Premium নিন মাত্র ৯৯ টাকায়</h3>
            <p style="color:white;font-size:1.5rem;font-weight:700">bKash: {BKASH_NUMBER}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⭐ Premium Activate করুন"):
            st.session_state.page = "premium"
            st.rerun()
    else:
        st.markdown('<div class="section-title">📁 ভিডিও আপলোড করুন</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("", type=["mp4","avi","mov","mpeg4"], label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="section-title">📥 মূল ভাষা</div>', unsafe_allow_html=True)
            source_lang = st.selectbox("", list(SOURCE_LANGUAGES.keys()), index=1,
                                        label_visibility="collapsed", key="src")
        with c2:
            st.markdown('<div class="section-title">📤 টার্গেট ভাষা</div>', unsafe_allow_html=True)
            opts = [l for l in TARGET_LANGUAGES if l != source_lang]
            selected_langs = st.multiselect("", opts, default=[opts[0]] if opts else [],
                                             label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">🎙️ কণ্ঠ বেছে নিন</div>', unsafe_allow_html=True)
        selected_voice = st.selectbox("", list(ALL_VOICES.keys()), label_visibility="collapsed", key="vc")

        cp, cs = st.columns([1, 2])
        with cp:
            if st.button("🔊 শুনুন"):
                vc   = ALL_VOICES[selected_voice]
                lang = vc[:2]
                prev = PREVIEW_TEXT.get(lang, PREVIEW_TEXT["en"])
                pp   = "/tmp/prev.mp3"
                with st.spinner("তৈরি হচ্ছে..."):
                    if text_to_speech(prev, vc, pp):
                        with open(pp, "rb") as f:
                            st.audio(f.read(), format="audio/mp3")
                    else:
                        st.warning("Preview হয়নি।")

        st.info(f"✅ নির্বাচিত: **{selected_voice}**")

        if not user_premium:
            st.warning(f"⚡ আজকের বাকি: {remaining}/3 ভিডিও")

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🚀 ডাবিং শুরু করুন"):
            if not uploaded_file:
                st.error("⚠️ ভিডিও আপলোড করুন!")
            elif not selected_langs:
                st.error("⚠️ টার্গেট ভাষা সিলেক্ট করুন!")
            elif not user_premium and today_usage >= FREE_LIMIT:
                st.error("⚠️ Limit শেষ!")
            else:
                vc       = ALL_VOICES[selected_voice]
                src_code = SOURCE_LANGUAGES[source_lang]
                vpath    = "/tmp/input_video.mp4"

                with open(vpath, "wb") as f:
                    f.write(uploaded_file.read())

                prog   = st.progress(0)
                status = st.empty()

                status.info("⏳ অডিও বের হচ্ছে...")
                subprocess.run(f'ffmpeg -i "{vpath}" -q:a 0 -map a /tmp/audio_src.mp3 -y',
                               shell=True, capture_output=True)
                prog.progress(20)

                status.info("⏳ AI টেক্সট বের করছে...")
                model  = whisper.load_model("base")
                result = model.transcribe("/tmp/audio_src.mp3", language=src_code)
                src_text = result["text"]
                prog.progress(40)

                vdur  = get_duration(vpath)
                step  = 60 // len(selected_langs)
                cur_p = 40
                dfiles = {}

                for lang_name in selected_langs:
                    dest_code = TARGET_LANGUAGES[lang_name]
                    status.info(f"⏳ {lang_name} ডাবিং হচ্ছে...")

                    translated  = translate_text(src_text, src_code, dest_code)
                    apath       = f"/tmp/audio_{dest_code}.mp3"
                    comp_voice  = get_compatible_voice(vc, dest_code)

                    if not text_to_speech(translated, comp_voice, apath):
                        text_to_speech_gtts(translated, dest_code, apath)

                    padded = f"/tmp/padded_{dest_code}.mp3"
                    adur   = get_duration(apath)

                    if adur > 0 and adur < vdur:
                        subprocess.run(
                            f'ffmpeg -i "{apath}" -af "apad=pad_dur={vdur-adur}" '
                            f'-t {vdur} "{padded}" -y',
                            shell=True, capture_output=True
                        )
                    else:
                        padded = apath

                    opath = f"/tmp/dubbed_{dest_code}.mp4"
                    subprocess.run(
                        f'ffmpeg -i "{vpath}" -i "{padded}" -c:v copy '
                        f'-map 0:v:0 -map 1:a:0 -t {vdur} "{opath}" -y',
                        shell=True, capture_output=True
                    )

                    cur_p += step
                    prog.progress(min(cur_p, 100))

                    if os.path.exists(opath):
                        with open(opath, "rb") as f:
                            dfiles[lang_name] = {
                                "bytes": f.read(),
                                "filename": f"DubIT_{dest_code}.mp4"
                            }

                inc_usage(uid)
                prog.progress(100)
                status.empty()
                st.session_state.dubbed_files  = dfiles
                st.session_state.dubbing_done  = True
                st.session_state.selected_voice = selected_voice
                st.rerun()

# ---- FOOTER ----
st.markdown("""
<div class="footer">
    <div class="footer-brand">Made with Hasibur Joy by House IT LTD</div>
    <div class="footer-sub">DubIT — Bangladesh's First AI Video Dubbing Tool</div>
</div>
""", unsafe_allow_html=True)
