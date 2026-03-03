import streamlit as st
import subprocess, os, whisper, json, uuid
from datetime import datetime, date
from gtts import gTTS
from deep_translator import GoogleTranslator, MyMemoryTranslator
import firebase_admin
from firebase_admin import credentials, firestore

@st.cache_resource(show_spinner=False)
def init_firebase():
    try:
        if not firebase_admin._apps:
            fb = st.secrets["firebase"]
            cred = credentials.Certificate({
                "type": fb["type"],
                "project_id": fb["project_id"],
                "private_key_id": fb["private_key_id"],
                "private_key": fb["private_key"].replace("\\n", "\n"),
                "client_email": fb["client_email"],
                "client_id": fb["client_id"],
                "auth_uri": fb["auth_uri"],
                "token_uri": fb["token_uri"],
                "client_x509_cert_url": fb["client_x509_cert_url"],
            })
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Firebase error: {e}")
        return None

db = init_firebase()

ALL_VOICES = {
    "👨 বাংলা পুরুষ — Pradeep":      "bn-BD-PradeepNeural",
    "👩 বাংলা মহিলা — Nabanita":     "bn-BD-NabanitaNeural",
    "👨 ইংরেজি পুরুষ — Guy":          "en-US-GuyNeural",
    "👨 ইংরেজি পুরুষ — Christopher":  "en-US-ChristopherNeural",
    "👨 ইংরেজি পুরুষ — Eric":         "en-US-EricNeural",
    "👩 ইংরেজি মহিলা — Jenny":        "en-US-JennyNeural",
    "👩 ইংরেজি মহিলা — Aria":         "en-US-AriaNeural",
    "👩 ইংরেজি মহিলা — Sara":         "en-US-SaraNeural",
    "👨 হিন্দি পুরুষ — Madhur":       "hi-IN-MadhurNeural",
    "👩 হিন্দি মহিলা — Swara":        "hi-IN-SwaraNeural",
    "👨 উর্দু পুরুষ — Asad":           "ur-PK-AsadNeural",
    "👩 উর্দু মহিলা — Uzma":           "ur-PK-UzmaNeural",
    "👨 টার্কিশ পুরুষ — Ahmet":       "tr-TR-AhmetNeural",
    "👩 টার্কিশ মহিলা — Emel":        "tr-TR-EmelNeural",
    "👨 আরবি পুরুষ — Hamed":          "ar-SA-HamedNeural",
    "👩 আরবি মহিলা — Zariyah":        "ar-SA-ZariyahNeural",
    "👨 ফ্রেঞ্চ পুরুষ — Henri":        "fr-FR-HenriNeural",
    "👩 ফ্রেঞ্চ মহিলা — Denise":       "fr-FR-DeniseNeural",
    "👨 জার্মান পুরুষ — Conrad":       "de-DE-ConradNeural",
    "👩 জার্মান মহিলা — Katja":        "de-DE-KatjaNeural",
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

BKASH_NUMBER = "01821282411"
FREE_LIMIT   = 3

# ---- FIREBASE HELPERS ----
def fb_get(collection, doc_id):
    try:
        if db is None: return None
        doc = db.collection(collection).document(doc_id).get()
        return doc.to_dict() if doc.exists else None
    except:
        return None

def fb_set(collection, doc_id, data):
    try:
        if db is None: return False
        db.collection(collection).document(doc_id).set(data)
        return True
    except:
        return False

def fb_update(collection, doc_id, data):
    try:
        if db is None: return False
        db.collection(collection).document(doc_id).update(data)
        return True
    except:
        return False

def fb_delete(collection, doc_id):
    try:
        if db is None: return False
        db.collection(collection).document(doc_id).delete()
        return True
    except:
        return False

def fb_get_all(collection):
    try:
        if db is None: return {}
        docs = db.collection(collection).stream()
        return {doc.id: doc.to_dict() for doc in docs}
    except:
        return {}

def is_premium(uid):
    data = fb_get("premium", uid)
    return data.get("active", False) if data else False

def get_usage(uid):
    data = fb_get("usage", uid)
    if not data: return 0
    return data.get(str(date.today()), 0)

def inc_usage(uid):
    today = str(date.today())
    data  = fb_get("usage", uid) or {}
    data[today] = data.get(today, 0) + 1
    fb_set("usage", uid, data)

def save_history(uid, info):
    data  = fb_get("history", uid) or {"items": []}
    items = data.get("items", [])
    items.insert(0, info)
    items = items[:20]
    fb_set("history", uid, {"items": items})

def get_history(uid):
    data = fb_get("history", uid)
    return data.get("items", []) if data else []

def register_user(email, password):
    if fb_get("users", email):
        return False, "এই email আগেই registered!"
    uid = str(uuid.uuid4())[:8]
    fb_set("users", email, {
        "password": password,
        "uid": uid,
        "joined": str(datetime.now())[:16],
        "role": "user"
    })
    return True, uid

def login_user(email, password):
    data = fb_get("users", email)
    if not data:                     return False, "Email পাওয়া যায়নি!"
    if data["password"] != password: return False, "Password ভুল!"
    return True, data

# ---- PAGE CONFIG ----
st.set_page_config(page_title="DubIT — AI Video Dubbing", page_icon="🎬", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp { background: #05050f; }
.hero {
    background: linear-gradient(135deg, #1a0533 0%, #0d1b4b 50%, #001a3a 100%);
    border: 1px solid rgba(139,92,246,0.3);
    border-radius: 28px;
    padding: 3rem 2rem;
    text-align: center;
    margin-bottom: 2rem;
}
.hero-badge {
    display: inline-block;
    background: rgba(139,92,246,0.15);
    border: 1px solid rgba(139,92,246,0.4);
    color: #a78bfa;
    padding: 0.35rem 1.2rem;
    border-radius: 50px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 1rem;
}
.hero h1 {
    font-size: 4rem !important;
    font-weight: 900 !important;
    background: linear-gradient(135deg, #ffffff 0%, #a78bfa 50%, #60a5fa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0.5rem 0 !important;
}
.hero p { color: #94a3b8; font-size: 1.1rem; margin: 0; }
.stats-row { display: flex; gap: 0.8rem; margin-bottom: 1.5rem; }
.stat-card {
    flex: 1;
    background: linear-gradient(135deg, #0d0d20, #141428);
    border: 1px solid rgba(139,92,246,0.15);
    border-radius: 18px;
    padding: 1.2rem 0.8rem;
    text-align: center;
}
.stat-number {
    font-size: 1.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1;
}
.stat-label { color: #4a5568; font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 0.4rem; }
.section-title { color: #94a3b8; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 2.5px; margin-bottom: 0.6rem; }
.auth-box { background: linear-gradient(135deg, #0d0d20, #141428); border: 1px solid rgba(139,92,246,0.2); border-radius: 20px; padding: 2rem; margin: 0.5rem 0; }
.history-card { background: linear-gradient(135deg, #0d0d20, #141428); border: 1px solid rgba(139,92,246,0.15); border-radius: 16px; padding: 1rem 1.2rem; margin-bottom: 0.8rem; border-left: 3px solid #7c3aed; }
.admin-stat { background: linear-gradient(135deg, #0d0d20, #141428); border: 1px solid rgba(139,92,246,0.2); border-radius: 16px; padding: 1.5rem; text-align: center; }
.admin-stat-num { font-size: 2.5rem; font-weight: 900; background: linear-gradient(135deg, #a78bfa, #60a5fa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.admin-stat-label { color: #64748b; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
.pending-card { background: linear-gradient(135deg, #1a0f00, #261a00); border: 1px solid rgba(251,191,36,0.3); border-radius: 14px; padding: 1.2rem; margin-bottom: 1rem; }
.plan-card-free { background: linear-gradient(135deg, #0d0d20, #141428); border: 1px solid rgba(100,116,139,0.2); border-radius: 20px; padding: 1.8rem; text-align: center; }
.plan-card-premium { background: linear-gradient(135deg, #1a0533, #0d1b4b); border: 2px solid rgba(139,92,246,0.5); border-radius: 20px; padding: 1.8rem; text-align: center; box-shadow: 0 0 30px rgba(139,92,246,0.1); }
.plan-price { font-size: 2.8rem; font-weight: 900; background: linear-gradient(135deg, #a78bfa, #60a5fa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; line-height: 1; margin: 0.5rem 0; }
.badge-premium { display: inline-block; background: linear-gradient(135deg, #7c3aed, #2563eb); color: white; padding: 0.3rem 1rem; border-radius: 50px; font-size: 0.75rem; font-weight: 700; }
.badge-free { display: inline-block; background: rgba(100,116,139,0.2); color: #64748b; padding: 0.3rem 1rem; border-radius: 50px; font-size: 0.75rem; font-weight: 700; }
.divider { height: 1px; background: linear-gradient(90deg, transparent, rgba(139,92,246,0.3), transparent); margin: 1.5rem 0; }
.stFileUploader > div { background: linear-gradient(135deg, #0d0d20, #141428) !important; border: 2px dashed rgba(139,92,246,0.3) !important; border-radius: 16px !important; }
.stMultiSelect > div > div,
.stSelectbox > div > div,
.stTextInput > div > div {
    background: #0d0d20 !important;
    border: 1px solid rgba(139,92,246,0.25) !important;
    border-radius: 12px !important;
    color: white !important;
    pointer-events: auto !important;
    z-index: 999 !important;
    position: relative !important;
}
.stMultiSelect [data-baseweb="select"],
.stSelectbox [data-baseweb="select"] {
    pointer-events: auto !important;
    cursor: pointer !important;
}
.stMultiSelect [data-baseweb="popover"],
.stSelectbox [data-baseweb="popover"] {
    z-index: 9999 !important;
    pointer-events: auto !important;
}
[data-testid="stAppViewContainer"] {
    pointer-events: auto !important;
}
div[data-baseweb="select"] > div {
    pointer-events: auto !important;
    cursor: pointer !important;
}
div[role="listbox"] {
    z-index: 99999 !important;
    pointer-events: auto !important;
    background: #0d0d20 !important;
}
div[role="option"] {
    pointer-events: auto !important;
    color: white !important;
    background: #0d0d20 !important;
}
div[role="option"]:hover {
    background: rgba(139,92,246,0.2) !important;
}
.stApp [data-stale="true"] {
    opacity: 1 !important;
    visibility: visible !important;
}
.stButton > button { background: linear-gradient(135deg, #7c3aed, #2563eb) !important; color: white !important; border: none !important; border-radius: 12px !important; padding: 0.8rem 1.5rem !important; font-size: 0.95rem !important; font-weight: 700 !important; width: 100% !important; box-shadow: 0 4px 15px rgba(124,58,237,0.3) !important; }
.stProgress > div > div { background: linear-gradient(135deg, #7c3aed, #2563eb) !important; border-radius: 10px !important; }
.stDownloadButton > button { background: linear-gradient(135deg, #065f46, #047857) !important; color: white !important; border: 1px solid rgba(16,185,129,0.3) !important; border-radius: 12px !important; font-weight: 700 !important; width: 100% !important; margin-bottom: 0.5rem !important; }
.stTabs [data-baseweb="tab-list"] { background: #0d0d20 !important; border-radius: 12px !important; padding: 4px !important; }
.stTabs [data-baseweb="tab"] { background: transparent !important; border-radius: 8px !important; color: #64748b !important; font-weight: 600 !important; }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg, #7c3aed, #2563eb) !important; color: white !important; }
.footer { text-align: center; padding: 2rem 0 1rem; margin-top: 3rem; }
.footer-brand { font-size: 1rem; font-weight: 700; background: linear-gradient(135deg, #a78bfa, #60a5fa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.footer-sub { color: #64748b; font-size: 0.8rem; margin-top: 0.3rem; }
footer { visibility: hidden; }
#MainMenu { visibility: hidden; }
header { visibility: hidden; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="manage-app-button"] { display: none !important; }
.stDeployButton { display: none !important; }
[class*="viewerBadge"] { display: none !important; }
[class*="viewer-badge"] { display: none !important; }
div[class*="ProfilePreview"] { display: none !important; }
.styles_viewerBadge__CvC9N { display: none !important; }
.viewerBadge_container__r5tak { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ---- SESSION STATE ----
for key, val in {
    "dubbed_files": {}, "dubbing_done": False, "selected_voice": "",
    "page": "login", "user_email": "", "user_uid": "", "is_admin": False
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ---- CORE FUNCTIONS ----
def text_to_speech(text, voice_code, output_path):
    try:
        tf = "/tmp/tts_input.txt"
        with open(tf, "w", encoding="utf-8") as f:
            f.write(text)
        subprocess.run(
            f'edge-tts --voice "{voice_code}" --file "{tf}" --write-media "{output_path}"',
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

def get_compatible_voice(vc, dest):
    return vc if vc[:2] == dest else LANG_DEFAULT_VOICE.get(dest, "en-US-GuyNeural")

def translate_text(text, src, dest):
    if src == dest: return text
    sentences = text.split('. ')
    chunks, cur = [], ""
    for s in sentences:
        if len(cur) + len(s) < 400: cur += s + ". "
        else: chunks.append(cur); cur = s + ". "
    if cur: chunks.append(cur)
    parts = []
    for chunk in chunks:
        if not chunk.strip(): continue
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

# ======================================
# ADMIN PANEL
# ======================================
query_params = st.query_params
is_admin_url = (
    query_params.get("panel") == "dubitadmin2024" or
    st.session_state.get("is_admin", False)
)

if is_admin_url:
    if not st.session_state.is_admin:
        st.markdown("""
        <div class="hero">
            <div class="hero-badge">SECURE ACCESS</div>
            <h1>🔑 Admin</h1>
            <p>DubIT Management Dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown('<div class="auth-box">', unsafe_allow_html=True)
            au = st.text_input("", placeholder="📧 Admin Email", key="au")
            ap = st.text_input("", type="password", placeholder="🔒 Password", key="ap")
            if st.button("🔑 Admin Login"):
                ok, res = login_user(au, ap)
                if ok and res.get("role") == "admin":
                    st.session_state.is_admin = True
                    st.rerun()
                else:
                    st.error("❌ Wrong credentials!")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        all_premium = fb_get_all("premium")
        all_users   = fb_get_all("users")
        all_history = fb_get_all("history")
        pending     = {k:v for k,v in all_premium.items() if not v.get("active", False)}
        active      = {k:v for k,v in all_premium.items() if v.get("active", False)}
        total_dubs  = sum(len(v.get("items", [])) for v in all_history.values())

        st.markdown("""
        <div class="hero">
            <div class="hero-badge">ADMIN DASHBOARD</div>
            <h1>DubIT</h1>
            <p>Management & Analytics — Firebase Powered</p>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="admin-stat"><div class="admin-stat-num">{len(all_users)}</div><div class="admin-stat-label">👥 Users</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="admin-stat"><div class="admin-stat-num" style="background:linear-gradient(135deg,#f59e0b,#ef4444);-webkit-background-clip:text;-webkit-text-fill-color:transparent">{len(pending)}</div><div class="admin-stat-label">⏳ Pending</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="admin-stat"><div class="admin-stat-num" style="background:linear-gradient(135deg,#10b981,#059669);-webkit-background-clip:text;-webkit-text-fill-color:transparent">{len(active)}</div><div class="admin-stat-label">⭐ Premium</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="admin-stat"><div class="admin-stat-num">{total_dubs}</div><div class="admin-stat-label">🎬 Dubs</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        monthly_rev = len(active) * 99
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0a2010,#0d2d1a);border:1px solid rgba(16,185,129,0.3);
        border-radius:16px;padding:1.2rem 1.5rem;margin-bottom:1.5rem;
        display:flex;justify-content:space-between;align-items:center">
            <div>
                <div style="color:#10b981;font-size:0.8rem;font-weight:700;letter-spacing:1px">MONTHLY REVENUE</div>
                <div style="color:white;font-size:2rem;font-weight:800">৳{monthly_rev}</div>
            </div>
            <div style="text-align:right">
                <div style="color:#64748b;font-size:0.8rem">Per User</div>
                <div style="color:#10b981;font-weight:700">৳99/month</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if pending:
            st.markdown(f'<div style="color:#f59e0b;font-size:0.85rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-bottom:1rem">⏳ Pending ({len(pending)})</div>', unsafe_allow_html=True)
            for uid, info in pending.items():
                st.markdown(f"""
                <div class="pending-card">
                    <div style="color:#fbbf24;font-weight:700">📧 {info.get('email','Unknown')}</div>
                    <div style="color:#94a3b8;font-size:0.85rem;margin-top:0.3rem">
                        UID: <code style="background:rgba(255,255,255,0.1);padding:2px 6px;border-radius:4px">{uid}</code> |
                        TXN: <code style="background:rgba(251,191,36,0.2);padding:2px 6px;border-radius:4px;color:#fbbf24">{info.get('txn_id')}</code> |
                        📅 {info.get('date','')[:16]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                ca, cb = st.columns(2)
                with ca:
                    if st.button(f"✅ Approve", key=f"ap_{uid}"):
                        fb_update("premium", uid, {"active": True})
                        st.success("✅ Approved!")
                        st.rerun()
                with cb:
                    if st.button(f"❌ Reject", key=f"rj_{uid}"):
                        fb_delete("premium", uid)
                        st.warning("Rejected!")
                        st.rerun()
        else:
            st.markdown('<div style="background:linear-gradient(135deg,#0d0d20,#141428);border:1px solid rgba(139,92,246,0.1);border-radius:14px;padding:1.5rem;text-align:center;color:#4a5568;margin-bottom:1rem">✅ কোনো pending request নেই</div>', unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        if all_users:
            st.markdown('<div style="color:#94a3b8;font-size:0.75rem;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;margin-bottom:1rem">👥 Registered Users</div>', unsafe_allow_html=True)
            st.markdown("""
            <div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr;
            background:rgba(139,92,246,0.1);border-radius:10px;padding:0.7rem 1rem;
            color:#a78bfa;font-size:0.75rem;font-weight:700;letter-spacing:1px;
            text-transform:uppercase;margin-bottom:0.5rem">
                <span>Email</span><span>Status</span><span>আজ</span><span>Joined</span>
            </div>
            """, unsafe_allow_html=True)
            for email, info in all_users.items():
                uid_u   = info.get("uid", "")
                prem    = is_premium(uid_u)
                usage_u = get_usage(uid_u)
                joined  = info.get("joined", "")[:10]
                badge   = '<span style="background:linear-gradient(135deg,#7c3aed,#2563eb);color:white;padding:2px 8px;border-radius:20px;font-size:0.7rem;font-weight:700">⭐ Premium</span>' if prem else '<span style="background:rgba(100,116,139,0.2);color:#64748b;padding:2px 8px;border-radius:20px;font-size:0.7rem">Free</span>'
                st.markdown(f"""
                <div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr;
                background:linear-gradient(135deg,#0d0d20,#141428);border:1px solid rgba(139,92,246,0.1);
                border-radius:10px;padding:0.8rem 1rem;margin-bottom:0.4rem;align-items:center">
                    <span style="color:#e2e8f0;font-size:0.85rem">{email}</span>
                    <span>{badge}</span>
                    <span style="color:#94a3b8;font-size:0.85rem">{usage_u} ভিডিও</span>
                    <span style="color:#4a5568;font-size:0.8rem">{joined}</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        cl, _, _ = st.columns(3)
        with cl:
            if st.button("🚪 Admin Logout"):
                st.session_state.is_admin = False
                st.rerun()

    st.stop()

# ======================================
# USER PANEL
# ======================================
st.markdown("""
<div class="hero">
    <div class="hero-badge">🇧🇩 Bangladesh's First</div>
    <h1>DubIT</h1>
    <p>যেকোনো ভিডিও → ৬ ভাষায় AI ডাবিং</p>
</div>
""", unsafe_allow_html=True)

if not st.session_state.user_uid:
    tab1, tab2 = st.tabs(["🔐  Login", "📝  Register"])

    with tab1:
        c1, c2, c3 = st.columns([1, 3, 1])
        with c2:
            st.markdown('<div class="auth-box">', unsafe_allow_html=True)
            st.markdown('<p style="color:#a78bfa;font-weight:700;font-size:1.1rem;margin-bottom:1rem">Welcome Back 👋</p>', unsafe_allow_html=True)
            le = st.text_input("", placeholder="📧 Email", key="le")
            lp = st.text_input("", type="password", placeholder="🔒 Password", key="lp")
            if st.button("🚀 Login করুন"):
                if not le or not lp:
                    st.error("Email ও Password দিন!")
                else:
                    ok, res = login_user(le, lp)
                    if ok:
                        st.session_state.user_email = le
                        st.session_state.user_uid   = res["uid"]
                        if res.get("role") == "admin":
                            st.session_state.is_admin = True
                        st.session_state.page = "main"
                        st.rerun()
                    else:
                        st.error(f"❌ {res}")
            st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        c1, c2, c3 = st.columns([1, 3, 1])
        with c2:
            st.markdown("""
            <div style="background:linear-gradient(135deg,#1a0533,#0d1b4b);
            border:1px solid rgba(139,92,246,0.4);border-radius:16px;
            padding:1.2rem;margin-bottom:1rem">
                <div style="display:flex;justify-content:space-around;margin-bottom:0.8rem">
                    <div style="text-align:center">
                        <div style="font-size:1.6rem">🎬</div>
                        <div style="color:#94a3b8;font-size:0.7rem;margin-top:0.2rem;font-weight:600">৬ ভাষা</div>
                    </div>
                    <div style="text-align:center">
                        <div style="font-size:1.6rem">🎙️</div>
                        <div style="color:#94a3b8;font-size:0.7rem;margin-top:0.2rem;font-weight:600">২০ কণ্ঠ</div>
                    </div>
                    <div style="text-align:center">
                        <div style="font-size:1.6rem">⚡</div>
                        <div style="color:#94a3b8;font-size:0.7rem;margin-top:0.2rem;font-weight:600">AI দ্রুত</div>
                    </div>
                    <div style="text-align:center">
                        <div style="font-size:1.6rem">🆓</div>
                        <div style="color:#94a3b8;font-size:0.7rem;margin-top:0.2rem;font-weight:600">ফ্রি শুরু</div>
                    </div>
                </div>
                <div style="background:rgba(139,92,246,0.12);border:1px solid rgba(139,92,246,0.25);
                border-radius:8px;padding:0.5rem;text-align:center">
                    <span style="color:#a78bfa;font-size:0.8rem;font-weight:600">
                        ✨ আজই শুরু করুন — প্রতিদিন ৩টি ভিডিও বিনামূল্যে
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('<div class="auth-box">', unsafe_allow_html=True)
            st.markdown('<p style="color:#a78bfa;font-weight:700;font-size:1.1rem;margin-bottom:1rem">Create Account ✨</p>', unsafe_allow_html=True)
            re_ = st.text_input("", placeholder="📧 Email", key="re_")
            rp  = st.text_input("", type="password", placeholder="🔒 Password (কমপক্ষে ৬ অক্ষর)", key="rp")
            rp2 = st.text_input("", type="password", placeholder="🔒 Confirm Password", key="rp2")
            if st.button("✅ Register করুন"):
                if not re_ or not rp:
                    st.error("সব field পূরণ করুন!")
                elif len(rp) < 6:
                    st.error("Password কমপক্ষে ৬ অক্ষর!")
                elif rp != rp2:
                    st.error("Password match করছে না!")
                elif "@" not in re_:
                    st.error("সঠিক email দিন!")
                else:
                    ok, res = register_user(re_, rp)
                    if ok:
                        st.success("✅ Registration সফল! এখন Login করুন।")
                    else:
                        st.error(f"❌ {res}")
            st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ---- LOGGED IN ----
uid          = st.session_state.user_uid
user_premium = is_premium(uid)
today_usage  = get_usage(uid)
remaining    = max(0, FREE_LIMIT - today_usage)

if user_premium:
    st.markdown("""<div class="stats-row">
        <div class="stat-card"><div class="stat-number">6+</div><div class="stat-label">ভাষা</div></div>
        <div class="stat-card"><div class="stat-number">20</div><div class="stat-label">কণ্ঠ</div></div>
        <div class="stat-card"><div class="stat-number">∞</div><div class="stat-label">Unlimited</div></div>
        <div class="stat-card"><div class="stat-number">⭐</div><div class="stat-label">Premium</div></div>
    </div>""", unsafe_allow_html=True)
    st.markdown(f'<div style="background:linear-gradient(135deg,#0a2010,#0d2d1a);border:1px solid rgba(16,185,129,0.3);border-radius:14px;padding:0.8rem 1.2rem;margin-bottom:1rem"><span style="color:#10b981;font-weight:700">⭐ Premium Member</span> <span style="color:#94a3b8;font-size:0.85rem">| {st.session_state.user_email}</span></div>', unsafe_allow_html=True)
else:
    st.markdown(f"""<div class="stats-row">
        <div class="stat-card"><div class="stat-number">6+</div><div class="stat-label">ভাষা</div></div>
        <div class="stat-card"><div class="stat-number">20</div><div class="stat-label">কণ্ঠ</div></div>
        <div class="stat-card"><div class="stat-number">FREE</div><div class="stat-label">ফ্রি</div></div>
        <div class="stat-card"><div class="stat-number">{remaining}/3</div><div class="stat-label">আজকের বাকি</div></div>
    </div>""", unsafe_allow_html=True)

cn1, cn2, cn3, cn4 = st.columns(4)
with cn1:
    if st.button("🎬 ডাবিং"):
        st.session_state.page = "main"
        st.session_state.dubbing_done = False
        st.rerun()
with cn2:
    if st.button("📋 ইতিহাস"):
        st.session_state.page = "history"
        st.rerun()
with cn3:
    if st.button("⭐ Premium"):
        st.session_state.page = "premium"
        st.rerun()
with cn4:
    if st.button("🚪 Logout"):
        st.session_state.user_email   = ""
        st.session_state.user_uid     = ""
        st.session_state.page         = "login"
        st.session_state.dubbing_done = False
        st.session_state.is_admin     = False
        st.rerun()

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ======================================
# HISTORY PAGE
# ======================================
if st.session_state.page == "history":
    history = get_history(uid)
    st.markdown('<div style="color:#94a3b8;font-size:0.75rem;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;margin-bottom:1.2rem">📋 আপনার ডাবিং ইতিহাস</div>', unsafe_allow_html=True)
    if not history:
        st.markdown('<div style="background:linear-gradient(135deg,#0d0d20,#141428);border:1px solid rgba(139,92,246,0.1);border-radius:16px;padding:3rem;text-align:center"><div style="font-size:3rem">🎬</div><div style="color:#4a5568;margin-top:1rem">এখনো কোনো ডাবিং করা হয়নি</div></div>', unsafe_allow_html=True)
    else:
        for i, h in enumerate(history):
            st.markdown(f"""
            <div class="history-card">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:0.5rem">
                    <div>
                        <div style="display:flex;align-items:center;gap:0.8rem;margin-bottom:0.5rem">
                            <span style="background:linear-gradient(135deg,#7c3aed,#2563eb);color:white;padding:3px 10px;border-radius:20px;font-size:0.72rem;font-weight:700">#{len(history)-i}</span>
                            <span style="color:#e2e8f0;font-weight:600">{h.get('filename','ভিডিও')}</span>
                        </div>
                        <div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:0.4rem">
                            <span style="background:rgba(139,92,246,0.1);color:#a78bfa;padding:3px 10px;border-radius:20px;font-size:0.75rem">📥 {h.get('src_lang','')}</span>
                            <span style="color:#4a5568">→</span>
                            <span style="background:rgba(96,165,250,0.1);color:#60a5fa;padding:3px 10px;border-radius:20px;font-size:0.75rem">📤 {h.get('target_langs','')}</span>
                        </div>
                        <div style="display:flex;flex-wrap:wrap;gap:0.5rem">
                            <span style="color:#64748b;font-size:0.78rem">🎙️ {h.get('voice','')}</span>
                            <span style="color:#4a5568">•</span>
                            <span style="color:#64748b;font-size:0.78rem">⏱️ {h.get('duration','0')}s</span>
                            <span style="color:#4a5568">•</span>
                            <span style="color:#64748b;font-size:0.78rem">📦 {h.get('size','')}</span>
                        </div>
                    </div>
                    <div style="text-align:right">
                        <div style="color:#4a5568;font-size:0.75rem">{h.get('time','')}</div>
                        <div style="color:#10b981;font-size:0.8rem;font-weight:600;margin-top:0.3rem">✅ Completed</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ======================================
# PREMIUM PAGE
# ======================================
elif st.session_state.page == "premium":
    if user_premium:
        st.markdown('<div style="background:linear-gradient(135deg,#0a2010,#0d2d1a);border:2px solid rgba(16,185,129,0.4);border-radius:20px;padding:2rem;text-align:center"><div style="font-size:3rem">⭐</div><h3 style="color:#10b981">আপনি ইতিমধ্যে Premium Member!</h3><p style="color:#94a3b8">Unlimited ডাবিং উপভোগ করুন</p></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="section-title">⭐ PREMIUM PLAN</div>', unsafe_allow_html=True)
        cf, cp_ = st.columns(2)
        with cf:
            st.markdown("""<div class="plan-card-free"><div class="badge-free">FREE</div><div class="plan-price">৳০</div><div style="color:#64748b;font-size:0.85rem;margin-bottom:1rem">প্রতি মাসে</div><hr style="border:none;border-top:1px solid rgba(255,255,255,0.05);margin:1rem 0"><div style="color:#94a3b8;font-size:0.9rem;line-height:2">✅ ৩টি ভিডিও/দিন<br>✅ ৬ ভাষা<br>✅ ২০টি কণ্ঠ<br>❌ Limited</div></div>""", unsafe_allow_html=True)
        with cp_:
            st.markdown("""<div class="plan-card-premium"><div class="badge-premium">⭐ PREMIUM</div><div class="plan-price">৳৯৯</div><div style="color:#a78bfa;font-size:0.85rem;margin-bottom:1rem">প্রতি মাসে</div><hr style="border:none;border-top:1px solid rgba(139,92,246,0.2);margin:1rem 0"><div style="color:#e2e8f0;font-size:0.9rem;line-height:2">✅ Unlimited ভিডিও<br>✅ ৬ ভাষা<br>✅ ২০টি কণ্ঠ<br>✅ Priority processing</div></div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0d0d20,#141428);border:1px solid rgba(139,92,246,0.2);border-radius:18px;padding:2rem;text-align:center;margin:1.5rem 0">
            <div style="color:#a78bfa;font-size:0.8rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-bottom:1rem">📱 bKash এ পেমেন্ট করুন</div>
            <div style="color:#94a3b8;margin-bottom:0.5rem">Send Money করুন:</div>
            <div style="color:white;font-size:2.2rem;font-weight:900;letter-spacing:4px;background:linear-gradient(135deg,#a78bfa,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent">{BKASH_NUMBER}</div>
            <div style="background:linear-gradient(135deg,#7c3aed,#2563eb);display:inline-block;color:white;padding:0.4rem 1.5rem;border-radius:50px;font-weight:700;margin:0.8rem 0">Amount: ৯৯ টাকা</div>
            <div style="color:#4a5568;font-size:0.8rem">bKash → Send Money → নম্বর দিন → ৯৯ টাকা</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-title">📋 Transaction ID দিন</div>', unsafe_allow_html=True)
        txn = st.text_input("", placeholder="যেমন: 8A3B9F2K1M", label_visibility="collapsed")
        if st.button("✅ Premium Activate করুন"):
            if not txn or len(txn) < 5:
                st.error("⚠️ সঠিক Transaction ID দিন!")
            else:
                all_p    = fb_get_all("premium")
                all_txns = [v.get("txn_id") for v in all_p.values()]
                if txn in all_txns:
                    st.error("⚠️ এই TXN ID আগেই ব্যবহার হয়েছে!")
                else:
                    fb_set("premium", uid, {
                        "active": False, "txn_id": txn,
                        "email": st.session_state.user_email,
                        "date": str(datetime.now())[:16]
                    })
                    st.success("✅ Request পাঠানো হয়েছে! Admin verify করলে Premium activate হবে।")

# ======================================
# DOWNLOAD PAGE
# ======================================
elif st.session_state.dubbing_done and st.session_state.dubbed_files:
    st.markdown('<div style="background:linear-gradient(135deg,#0a2010,#0d2d1a);border:1px solid rgba(16,185,129,0.3);border-radius:16px;padding:1.5rem;text-align:center;margin-bottom:1.5rem"><div style="font-size:2.5rem">🎉</div><div style="color:#10b981;font-size:1.2rem;font-weight:700">ডাবিং সফলভাবে সম্পন্ন!</div></div>', unsafe_allow_html=True)
    st.info(f"🎙️ ব্যবহৃত কণ্ঠ: **{st.session_state.selected_voice}**")
    for lang_name, data in st.session_state.dubbed_files.items():
        st.download_button(
            label=f"⬇️ {lang_name} ভিডিও ডাউনলোড করুন",
            data=data["bytes"], file_name=data["filename"],
            mime="video/mp4", key=f"dl_{lang_name}"
        )
    if st.button("🔄 নতুন ভিডিও ডাব করুন"):
        st.session_state.dubbed_files = {}
        st.session_state.dubbing_done = False
        st.session_state.page = "main"
        st.rerun()

# ======================================
# MAIN DUBBING PAGE
# ======================================
else:
    if not user_premium and today_usage >= FREE_LIMIT:
        st.markdown(f'<div style="background:linear-gradient(135deg,#1a0533,#0d1b4b);border:2px solid rgba(139,92,246,0.4);border-radius:20px;padding:2.5rem;text-align:center"><div style="font-size:2.5rem">⚠️</div><h3 style="color:#a78bfa">আজকের ফ্রি limit শেষ!</h3><p style="color:#94a3b8">মাত্র ৯৯ টাকায় Unlimited ডাবিং</p><div style="color:white;font-size:1.8rem;font-weight:800;letter-spacing:3px;margin:1rem 0">bKash: {BKASH_NUMBER}</div></div>', unsafe_allow_html=True)
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
        selected_voice = st.selectbox("", list(ALL_VOICES.keys()),
                                       label_visibility="collapsed", key="vc")

        cp_, cs_ = st.columns([1, 2])
        with cp_:
            if st.button("🔊 শুনুন"):
                vc = ALL_VOICES[selected_voice]
                pp = "/tmp/prev.mp3"
                with st.spinner("তৈরি হচ্ছে..."):
                    if text_to_speech(PREVIEW_TEXT.get(vc[:2], PREVIEW_TEXT["en"]), vc, pp):
                        with open(pp, "rb") as f:
                            st.audio(f.read(), format="audio/mp3")

        st.markdown(f'<div style="background:rgba(139,92,246,0.08);border:1px solid rgba(139,92,246,0.2);border-radius:10px;padding:0.7rem 1rem;margin:0.5rem 0;color:#a78bfa;font-size:0.9rem;font-weight:600">✅ নির্বাচিত: {selected_voice}</div>', unsafe_allow_html=True)

        if not user_premium:
            st.markdown(f'<div style="background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.2);border-radius:10px;padding:0.7rem 1rem;margin:0.5rem 0;color:#fbbf24;font-size:0.85rem">⚡ আজকের বাকি: {remaining}/3 ভিডিও</div>', unsafe_allow_html=True)

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
                model    = whisper.load_model("base")
                result   = model.transcribe("/tmp/audio_src.mp3", language=src_code)
                src_text = result["text"]
                prog.progress(40)

                vdur  = get_duration(vpath)
                step  = 60 // len(selected_langs)
                cur_p = 40
                dfiles = {}
                fsize  = round(os.path.getsize(vpath) / (1024*1024), 1)

                for lang_name in selected_langs:
                    dest_code  = TARGET_LANGUAGES[lang_name]
                    status.info(f"⏳ {lang_name} ডাবিং হচ্ছে...")
                    translated = translate_text(src_text, src_code, dest_code)
                    apath      = f"/tmp/audio_{dest_code}.mp3"
                    comp_voice = get_compatible_voice(vc, dest_code)
                    if not text_to_speech(translated, comp_voice, apath):
                        text_to_speech_gtts(translated, dest_code, apath)

                    padded = f"/tmp/padded_{dest_code}.mp3"
                    adur   = get_duration(apath)
                    if adur > 0 and adur < vdur:
                        subprocess.run(
                            f'ffmpeg -i "{apath}" -af "apad=pad_dur={vdur-adur}" -t {vdur} "{padded}" -y',
                            shell=True, capture_output=True
                        )
                    else:
                        padded = apath

                    opath = f"/tmp/dubbed_{dest_code}.mp4"
                    subprocess.run(
                        f'ffmpeg -i "{vpath}" -i "{padded}" -c:v copy -map 0:v:0 -map 1:a:0 -t {vdur} "{opath}" -y',
                        shell=True, capture_output=True
                    )
                    cur_p += step
                    prog.progress(min(cur_p, 100))

                    if os.path.exists(opath):
                        with open(opath, "rb") as f:
                            dfiles[lang_name] = {"bytes": f.read(), "filename": f"DubIT_{dest_code}.mp4"}

                save_history(uid, {
                    "filename":     uploaded_file.name,
                    "src_lang":     source_lang,
                    "target_langs": ", ".join(selected_langs),
                    "voice":        selected_voice,
                    "duration":     round(vdur, 1),
                    "size":         f"{fsize} MB",
                    "time":         str(datetime.now())[:16]
                })
                inc_usage(uid)
                prog.progress(100)
                status.empty()
                st.session_state.dubbed_files   = dfiles
                st.session_state.dubbing_done   = True
                st.session_state.selected_voice = selected_voice
                st.rerun()

st.markdown("""
<div class="footer">
    <div class="footer-brand">Made with Hasibur Joy by House IT LTD</div>
    <div class="footer-sub">DubIT — Bangladesh's First AI Video Dubbing Tool</div>
</div>
""", unsafe_allow_html=True)
