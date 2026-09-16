
import streamlit as st
from datetime import datetime
from pathlib import Path
import hashlib
import requests
import os
from urllib.parse import quote

APP_TITLE = "EKA DHANTHAYA MANDAP"
RECEIPT_DIR = Path("receipts")
RECEIPT_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="EDM | Virtual Chandha",
    page_icon="ðŸ•‰ï¸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Styling ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;600;700;800&family=Poppins:wght@400;500;600;700&display=swap');

:root {
  --saffron:#F57C00;
  --deep-saffron:#D95F02;
  --gold:#D89B18;
  --cream:#FFF8E7;
  --maroon:#7A1F1F;
  --brown:#4B2412;
  --green:#18864B;
  --red:#C62828;
}

html, body, [class*="css"] {
  font-family: 'Poppins', sans-serif;
}
.stApp {
  background:
    radial-gradient(circle at 10% 5%, rgba(255,193,7,.18), transparent 24%),
    radial-gradient(circle at 95% 10%, rgba(245,124,0,.14), transparent 25%),
    linear-gradient(180deg,#FFFDF7 0%,#FFF7E4 48%,#FFFDF8 100%);
  color:#3E2723 !important;
}
.block-container { padding-top: 1.2rem; max-width: 1250px; }

section[data-testid="stSidebar"] {
  background: linear-gradient(180deg,#FFF3D0 0%,#FFE8B0 52%,#FFF7E5 100%);
  border-right: 2px solid #E5B64B;
}
section[data-testid="stSidebar"] * { color:#4B2412 !important; }

.hero {
  background: linear-gradient(135deg,#FFF3CD,#FFE0A3);
  border: 2px solid #E3AA32;
  border-radius: 24px;
  padding: 22px 24px;
  box-shadow: 0 8px 25px rgba(130,80,0,.10);
  margin-bottom: 22px;
  position:relative;
  overflow:hidden;
}
.hero:after {
  content:"ðŸª·  ðŸ•‰ï¸  ðŸª·";
  position:absolute; right:22px; top:20px;
  font-size:28px; opacity:.32;
}
.hero .om { font-size:44px; }
.hero h1 { margin:0; color:#8A3B00 !important; font-size:34px; font-weight:800; }
.hero p { margin:4px 0 0; color:#7A4A16 !important; font-weight:600; }

.metric {
  background:#FFFFFF;
  border:1px solid #E9C56A;
  border-radius:18px;
  padding:18px;
  box-shadow:0 5px 18px rgba(110,70,0,.08);
}
.metric .label { color:#8A5A18; font-size:14px; font-weight:600; }
.metric .value { color:#7A1F1F; font-size:30px; font-weight:800; margin-top:3px; }

.card {
  background:rgba(255,255,255,.95);
  border:1px solid #E7C46C;
  border-radius:18px;
  padding:18px;
  box-shadow:0 5px 18px rgba(110,70,0,.07);
  margin-bottom:14px;
}
.section-title { color:#8A3B00 !important; font-size:30px; font-weight:800; }
.small-note { color:#7A5B32 !important; }

div.stButton > button {
  background: linear-gradient(135deg,#F57C00,#E65100) !important;
  color:#FFFFFF !important;
  border:0 !important;
  border-radius:12px !important;
  font-weight:700 !important;
  min-height:42px;
  box-shadow:0 4px 10px rgba(230,81,0,.18);
}
div.stButton > button:hover {
  background: linear-gradient(135deg,#FF9800,#D84315) !important;
  color:#FFFFFF !important;
}
div[data-testid="stFormSubmitButton"] button {
  background:linear-gradient(135deg,#D89B18,#F57C00) !important;
}
.stTextInput label, .stTextArea label, .stNumberInput label,
.stSelectbox label, .stRadio label { color:#5D4037 !important; font-weight:600 !important; }
input, textarea, [data-baseweb="select"] > div {
  background:#FFFFFF !important;
  color:#3E2723 !important;
  border-color:#E3B34D !important;
}
[data-testid="stMetricValue"], [data-testid="stMetricLabel"] { color:#7A1F1F !important; }

.login-wrap {
  max-width:520px; margin:55px auto;
  background:#FFFFFF; border:2px solid #E2B44A; border-radius:26px;
  padding:34px; text-align:center;
  box-shadow:0 14px 40px rgba(111,67,0,.13);
}
.login-om { font-size:64px; }
.login-title { color:#8A3B00 !important; font-size:28px; font-weight:800; margin:5px 0; }
.login-sub { color:#7A5B32 !important; margin-bottom:22px; }

[data-testid="stAlert"] { border-radius:14px; }
footer { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()


def sb_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def sb_ready():
    return bool(SUPABASE_URL and SUPABASE_KEY)


def sb_get(path, params=None):
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/{path}", headers=sb_headers(), params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


def sb_post(path, payload):
    resp = requests.post(f"{SUPABASE_URL}/rest/v1/{path}", headers=sb_headers(), json=payload, timeout=20)
    resp.raise_for_status()
    return resp.json()


def sb_patch(path, params, payload):
    resp = requests.patch(f"{SUPABASE_URL}/rest/v1/{path}", headers=sb_headers(), params=params, json=payload, timeout=20)
    resp.raise_for_status()
    return resp.json()


def get_donors(status=None):
    params = {"select": "*", "order": "id.desc"}
    if status:
        params["status"] = f"eq.{status}"
    return sb_get("donors", params)


def get_donor_by_receipt(receipt_no):
    rows = sb_get("donors", {
        "select": "*",
        "receipt_no": f"eq.{receipt_no}",
        "status": "eq.Paid",
        "limit": "1",
    })
    return rows[0] if rows else None


def next_receipt_number():
    rows = sb_get("donors", {"select": "id", "order": "id.desc", "limit": "1"})
    next_id = (int(rows[0]["id"]) + 1) if rows else 1
    return f"EDM-{datetime.now().year}-{next_id:05d}"


def save_donor(name, address, phone, amount, mode, status):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    receipt = next_receipt_number()
    payload = {
        "receipt_no": receipt,
        "name": name.strip(),
        "address": address.strip(),
        "phone": phone.strip(),
        "amount": float(amount),
        "mode": mode,
        "status": status,
        "created_at": now,
        "paid_at": now if status == "Paid" else None,
        "sms_sent": False,
    }
    rows = sb_post("donors", payload)
    return rows[0]


def mark_paid(donor_id):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = sb_patch("donors", {"id": f"eq.{donor_id}"}, {"status": "Paid", "paid_at": now})
    return rows[0] if rows else None


def ensure_cloud_database():
    if not sb_ready():
        st.error("Cloud database is not configured. Add SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in Render Environment Variables.")
        st.stop()

def receipt_text(r):
    return f"""à¥¥ à¤¶à¥à¤°à¥€ à¤—à¤£à¥‡à¤¶à¤¾à¤¯ à¤¨à¤®à¤ƒ à¥¥

EKA DHANTHAYA MANDAP
ESTD. 2016
GANESH CHANDHA RECEIPT
================================
Receipt No : {r['receipt_no']}
Date       : {r['paid_at'] or r['created_at']}
Name       : {r['name']}
Phone      : {r['phone']}
Address    : {r['address']}
Amount     : Rs. {r['amount']:.2f}
Payment    : {r['mode']}
Status     : PAID
================================
Thank you for your contribution.
à¥¥ à¤—à¤£à¤ªà¤¤à¤¿ à¤¬à¤¾à¤ªà¥à¤ªà¤¾ à¤®à¥‹à¤°à¤¯à¤¾ à¥¥ ðŸ™
"""
def receipt_url(r):
    base = os.getenv("APP_URL", "").strip().rstrip("/")
    if not base:
        return ""
    return f"{base}/?receipt={quote(str(r['receipt_no']))}"

def sms_message(r):
    url = receipt_url(r)
    msg = (
        f"ðŸ™ EKA DHANTHAYA MANDAP - ESTD. 2016\\n"
        f"Chandha payment received successfully.\\n"
        f"Name: {r['name']}\\n"
        f"Amount: Rs. {r['amount']:.0f}\\n"
        f"Receipt No: {r['receipt_no']}\\n"
        f"Payment: {r['mode']}\\n"
    )
    if url:
        msg += f"View / Download Receipt: {url}\\n"
    msg += "Thank you for your contribution.\\nGanapati Bappa Morya ðŸ™"
    return msg


def receipt_card(r):
    st.markdown(f"""
    <div style="background:#FFF8E7;border:3px solid #D89B18;border-radius:18px;
                padding:24px;max-width:760px;margin:10px auto;text-align:center;">
      <div style="font-size:26px;color:#7A1F1F;font-weight:800;">à¥¥ à¤¶à¥à¤°à¥€ à¤—à¤£à¥‡à¤¶à¤¾à¤¯ à¤¨à¤®à¤ƒ à¥¥</div>
      <div style="font-size:30px;color:#8A3B00;font-weight:800;">EKA DHANTHAYA MANDAP</div>
      <div style="color:#7A4A16;font-weight:700;">ESTD. 2016</div>
      <hr>
      <div style="font-size:22px;color:#7A1F1F;font-weight:800;">GANESH CHANDHA RECEIPT</div>
      <p><b>Receipt No:</b> {r['receipt_no']} &nbsp; | &nbsp; <b>Date:</b> {r['paid_at'] or r['created_at']}</p>
      <p style="text-align:left;"><b>Name:</b> {r['name']}<br>
      <b>Address:</b> {r['address']}<br>
      <b>Phone:</b> {r['phone']}<br>
      <b>Amount:</b> â‚¹{r['amount']:,.0f}<br>
      <b>Payment Mode:</b> {r['mode']}<br>
      <b>Status:</b> PAID</p>
      <hr>
      <div style="color:#7A1F1F;font-weight:800;">à¥¥ à¤—à¤£à¤ªà¤¤à¤¿ à¤¬à¤¾à¤ªà¥à¤ªà¤¾ à¤®à¥‹à¤°à¤¯à¤¾ à¥¥ ðŸ™</div>
    </div>
    """, unsafe_allow_html=True)


def sms_link(r, label="ðŸ“± SEND SMS"):
    phone = "91" + r["phone"].strip()
    body = quote(sms_message(r))
    return (
        f'<a href="sms:{phone}?body={body}" '
        f'style="display:inline-block;padding:10px 14px;background:#F57C00;'
        f'color:white;text-decoration:none;border-radius:10px;font-weight:700;'
        f'margin:3px 0;">{label}</a>'
    )


def login():
    st.markdown("""
    <div class="login-wrap">
      <div class="login-om">ðŸ•‰ï¸</div>
      <div class="login-title">EKA DHANTHAYA MANDAP</div>
      <div class="login-sub">Virtual Chandha â€¢ ESTD. 2016</div>
    </div>
    """, unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Username", placeholder="Enter username")
        p = st.text_input("Password", type="password", placeholder="Enter password")
        ok = st.form_submit_button("ðŸ” LOGIN", use_container_width=True)
    if ok:
        if u == "EDM" and p == "Edm@2016":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Invalid username or password.")

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    receipt_no = st.query_params.get("receipt")
    if receipt_no:
        ensure_cloud_database()
        r_public = get_donor_by_receipt(receipt_no)
        if r_public:
            st.markdown("""
            <div style="text-align:center;padding:22px 0;">
              <div style="font-size:46px;">ðŸ•‰ï¸</div>
              <h1 style="color:#8A3B00;">EKA DHANTHAYA MANDAP</h1>
              <p style="color:#7A5B32;font-weight:700;">Official Chandha Receipt</p>
            </div>
            """, unsafe_allow_html=True)
            receipt_card(r_public)
            st.info("You can take a screenshot or use your browser's Print / Save as PDF option.")
            st.stop()
        else:
            st.error("Receipt not found or payment is not yet confirmed.")
            st.stop()
    login()
    st.stop()

ensure_cloud_database()

# Sidebar
st.sidebar.success("â˜ï¸ Cloud database connected")
st.sidebar.markdown("""
<div style="text-align:center;padding:8px 0 18px">
  <div style="font-size:46px">ðŸ•‰ï¸</div>
  <div style="font-size:20px;font-weight:800;color:#8A3B00">EKA DHANTHAYA</div>
  <div style="font-size:16px;font-weight:700;color:#A45A00">MANDAP</div>
  <div style="font-size:12px;color:#7A5B32">ESTD. 2016</div>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "MENU",
    ["ðŸ  Dashboard", "âž• Add Chandha", "âœ… Paid Members", "â³ Pending Members", "ðŸ§¾ Receipts"],
)
if st.sidebar.button("ðŸšª Logout", use_container_width=True):
    st.session_state.auth = False
    st.rerun()

# Header
st.markdown("""
<div class="hero">
  <div class="om">ðŸ•‰ï¸</div>
  <h1>EKA DHANTHAYA MANDAP</h1>
  <p>Virtual Chandha Management â€¢ ESTD. 2016</p>
</div>
""", unsafe_allow_html=True)

if page == "ðŸ  Dashboard":
    rows = get_donors()
    paid = [r for r in rows if r["status"] == "Paid"]
    pending = [r for r in rows if r["status"] == "Not Paid"]
    collected = sum(r["amount"] for r in paid)
    pending_amt = sum(r["amount"] for r in pending)

    st.markdown('<div class="section-title">ðŸ™ Chandha Dashboard</div>', unsafe_allow_html=True)
    st.caption("Manage Ganesh festival contributions in one simple place.")

    c = st.columns(4)
    metrics = [
        ("ðŸ‘¥ Total Members", len(rows)),
        ("âœ… Paid Members", len(paid)),
        ("â³ Pending Members", len(pending)),
        ("ðŸ’° Total Collection", f"â‚¹{collected:,.0f}"),
    ]
    for col, (label, value) in zip(c, metrics):
        col.markdown(f'<div class="metric"><div class="label">{label}</div><div class="value">{value}</div></div>', unsafe_allow_html=True)

    st.markdown(f'<div class="card" style="margin-top:18px"><b>â³ Pending Amount:</b> â‚¹{pending_amt:,.0f}<br><span class="small-note">Pending members remain here until their payment is confirmed.</span></div>', unsafe_allow_html=True)

elif page == "âž• Add Chandha":
    st.markdown('<div class="section-title">âž• Add Chandha</div>', unsafe_allow_html=True)
    st.caption("Enter donor details and select whether the contribution is paid or pending. Paid entries can be sent by free phone SMS.")
    with st.form("add"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Name *")
            phone = st.text_input("Phone Number *", placeholder="10-digit mobile number")
            amount = st.number_input("Amount (â‚¹) *", min_value=1.0, step=50.0)
        with c2:
            address = st.text_area("Address *", height=122)
            mode = st.selectbox("Mode of Payment", ["Cash", "UPI", "Google Pay", "PhonePe", "Other"])
        status = st.radio("Payment Status", ["Paid", "Not Paid"], horizontal=True)
        submit = st.form_submit_button("ðŸ™ SAVE CHANDHA", use_container_width=True)

    if submit:
        if not name.strip() or not phone.strip() or not address.strip() or amount <= 0:
            st.error("Please fill Name, Phone Number, Address and Amount.")
        elif not phone.strip().isdigit() or len(phone.strip()) != 10:
            st.error("Please enter a valid 10-digit Indian mobile number.")
        else:
            try:
                r = save_donor(name, address, phone, amount, mode, status)
                receipt = r["receipt_no"]
            except Exception as e:
                st.error(f"Could not save donor: {e}")
                st.stop()
            if status == "Paid":
                st.success(f"âœ… Payment recorded. Receipt {receipt} is ready.")
                b1, b2 = st.columns(2)
                with b1:
                    st.download_button("ðŸ§¾ Download Receipt", receipt_text(r).encode(), f"{receipt}.txt", "text/plain")
                with b2:
                    st.markdown(sms_link(r, "ðŸ“± SEND SMS"), unsafe_allow_html=True)
                st.caption("SMS is prepared in your phone's Messages app. You must press Send. The message includes the receipt link when APP_URL is configured.")
            else:
                st.warning("â³ Saved to Pending Members.")

elif page in ["âœ… Paid Members", "â³ Pending Members"]:
    is_pending = page.startswith("â³")
    st.markdown(f'<div class="section-title">{"â³ Pending Members" if is_pending else "âœ… Paid Members"}</div>', unsafe_allow_html=True)
    search = st.text_input("ðŸ”Ž Search by name or phone", placeholder="Type a name or phone number...")
    rows = get_donors("Not Paid" if is_pending else "Paid")
    shown = 0
    for r in rows:
        if search and search.lower() not in (r["name"] + " " + r["phone"]).lower():
            continue
        shown += 1
        with st.container(border=True):
            cols = st.columns([3, 2, 1.5, 1.5, 1.8])
            cols[0].markdown(f"**{r['name']}**  \nðŸ“ {r['address']}")
            cols[1].markdown(f"ðŸ“ž **{r['phone']}**")
            cols[2].markdown(f"ðŸ’° **â‚¹{r['amount']:,.0f}**")
            cols[3].markdown(f"**{r['mode']}**")
            if is_pending:
                if cols[4].button("âœ… MARK PAID", key=f"pay{r['id']}"):
                    try:
                        updated = mark_paid(r["id"])
                        st.success(f"{r['name']} marked as paid. Receipt {r['receipt_no']} generated.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not update payment: {e}")
            else:
                with cols[4]:
                    st.download_button("ðŸ§¾ RECEIPT", receipt_text(r).encode(), f"{r['receipt_no']}.txt", "text/plain", key=f"rec{r['id']}")
                    st.markdown(sms_link(r), unsafe_allow_html=True)
    if shown == 0:
        st.info("No members found.")

elif page == "ðŸ§¾ Receipts":
    st.markdown('<div class="section-title">ðŸ§¾ Receipts</div>', unsafe_allow_html=True)
    q = st.text_input("ðŸ”Ž Search receipt / name / phone", placeholder="EDM-2026-00001")
    rows = get_donors("Paid")
    shown = 0
    for r in rows:
        if q and q.lower() not in (r["receipt_no"] + " " + r["name"] + " " + r["phone"]).lower():
            continue
        shown += 1
        with st.container(border=True):
            a,b,c,d = st.columns([2.5,2,1.3,1.5])
            a.markdown(f"**{r['receipt_no']}**  \n{r['name']}")
            b.markdown(f"ðŸ“ž {r['phone']}")
            c.markdown(f"â‚¹{r['amount']:,.0f}")
            d.download_button("â¬‡ï¸ Receipt", receipt_text(r).encode(), f"{r['receipt_no']}.txt", "text/plain", key=f"d{r['id']}")
            st.markdown(sms_link(r), unsafe_allow_html=True)
    if shown == 0:
        st.info("No receipts found.")

st.markdown("""
<div style="text-align:center;padding:30px 0 8px;color:#8A6A3B;font-size:12px">
ðŸ™ Ganapati Bappa Moriya â€¢ EKA DHANTHAYA MANDAP â€¢ ESTD. 2016 ðŸ™
</div>
""", unsafe_allow_html=True)
