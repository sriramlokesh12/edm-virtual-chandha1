import io
import os
import hashlib
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

APP_TITLE = "EKA DHANTHAYA MANDAP"
TEMPLATE_PATH = Path(__file__).parent / "receipt_template.jpg"

st.set_page_config(page_title="EDM | Virtual Chandha", page_icon="🕉️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');
:root{--saffron:#F57C00;--gold:#D89B18;--cream:#FFF8E7;--maroon:#7A1F1F;--brown:#4B2412}
html,body,[class*="css"]{font-family:Poppins,sans-serif}
.stApp{background:linear-gradient(180deg,#FFFDF7,#FFF7E4 48%,#FFFDF8);color:#3E2723!important}
.block-container{padding-top:1.2rem;max-width:1250px}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#FFF3D0,#FFE8B0 52%,#FFF7E5);border-right:2px solid #E5B64B}
section[data-testid="stSidebar"] *{color:#4B2412!important}
.hero{background:linear-gradient(135deg,#FFF3CD,#FFE0A3);border:2px solid #E3AA32;border-radius:24px;padding:22px 24px;box-shadow:0 8px 25px rgba(130,80,0,.10);margin-bottom:22px}
.hero h1{margin:0;color:#8A3B00!important;font-size:34px;font-weight:800}.hero p{margin:4px 0;color:#7A4A16!important;font-weight:600}.hero .om{font-size:42px}
.metric{background:#fff;border:1px solid #E9C56A;border-radius:18px;padding:18px;box-shadow:0 5px 18px rgba(110,70,0,.08)}
.metric .label{color:#8A5A18;font-size:14px;font-weight:600}.metric .value{color:#7A1F1F;font-size:30px;font-weight:800}
.section-title{color:#8A3B00!important;font-size:30px;font-weight:800}.card{background:#fff;border:1px solid #E7C46C;border-radius:18px;padding:18px;box-shadow:0 5px 18px rgba(110,70,0,.07);margin-bottom:14px}
div.stButton>button{background:linear-gradient(135deg,#F57C00,#E65100)!important;color:#fff!important;border:0!important;border-radius:12px!important;font-weight:700!important;min-height:42px}
div[data-testid="stFormSubmitButton"] button{background:linear-gradient(135deg,#D89B18,#F57C00)!important}
.stTextInput label,.stTextArea label,.stNumberInput label,.stSelectbox label,.stRadio label{color:#5D4037!important;font-weight:600!important}
input,textarea,[data-baseweb="select"]>div{background:#fff!important;color:#3E2723!important;border-color:#E3B34D!important}
.login-wrap{max-width:520px;margin:55px auto 20px;background:#fff;border:2px solid #E2B44A;border-radius:26px;padding:34px;text-align:center;box-shadow:0 14px 40px rgba(111,67,0,.13)}
.login-om{font-size:64px}.login-title{color:#8A3B00!important;font-size:28px;font-weight:800}.login-sub{color:#7A5B32!important}
footer{visibility:hidden}
</style>
""", unsafe_allow_html=True)

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
ADMIN_USERNAME = os.getenv("EDM_ADMIN_USERNAME", "EDM")
ADMIN_PASSWORD = os.getenv("EDM_ADMIN_PASSWORD", "EDM@2026")


def sb_headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}

def sb_ready(): return bool(SUPABASE_URL and SUPABASE_KEY)

def sb_get(path, params=None):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{path}", headers=sb_headers(), params=params, timeout=20); r.raise_for_status(); return r.json()

def sb_post(path, payload):
    r = requests.post(f"{SUPABASE_URL}/rest/v1/{path}", headers=sb_headers(), json=payload, timeout=20); r.raise_for_status(); return r.json()

def sb_patch(path, params, payload):
    r = requests.patch(f"{SUPABASE_URL}/rest/v1/{path}", headers=sb_headers(), params=params, json=payload, timeout=20); r.raise_for_status(); return r.json()

def ensure_cloud_database():
    if not sb_ready(): st.error("Cloud database is not configured. Add SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in Render Environment Variables."); st.stop()

def get_donors(status=None):
    params={"select":"*","order":"id.desc"}
    if status: params["status"]=f"eq.{status}"
    return sb_get("donors",params)

def get_donor_by_receipt(receipt_no):
    rows=sb_get("donors",{"select":"*","receipt_no":f"eq.{receipt_no}","status":"eq.Paid","limit":"1"})
    return rows[0] if rows else None

def next_receipt_number():
    rows=sb_get("donors",{"select":"id","order":"id.desc","limit":"1"})
    next_id=(int(rows[0]["id"])+1) if rows else 1
    return f"EDM-{datetime.now().year}-{next_id:05d}"

def save_donor(name,address,phone,amount,mode,status):
    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"); receipt=next_receipt_number()
    payload={"receipt_no":receipt,"name":name.strip(),"address":address.strip(),"phone":phone.strip(),"amount":float(amount),"mode":mode,"status":status,"created_at":now,"paid_at":now if status=="Paid" else None,"sms_sent":False}
    return sb_post("donors",payload)[0]

def mark_paid(donor_id):
    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows=sb_patch("donors",{"id":f"eq.{donor_id}"},{"status":"Paid","paid_at":now})
    return rows[0] if rows else None


def font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        if Path(p).exists(): return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def draw_wrapped(draw, text, xy, max_width, fnt, fill=(55,32,18), line_gap=7):
    words=str(text or "").split()
    lines=[]; line=""
    for word in words:
        test=(line+" "+word).strip()
        if draw.textbbox((0,0),test,font=fnt)[2] <= max_width or not line: line=test
        else: lines.append(line); line=word
    if line: lines.append(line)
    x,y=xy
    for ln in lines:
        draw.text((x,y),ln,font=fnt,fill=fill)
        y += fnt.size + line_gap


def receipt_image(r):
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError("receipt_template.jpg is missing from the project")
    img=Image.open(TEMPLATE_PATH).convert("RGB")
    d=ImageDraw.Draw(img)
    dark=(55,32,18); maroon=(105,20,20); gold=(115,72,10)
    # Coordinates correspond to the supplied 1536x1024 reference receipt.
    d.text((1340,89), str(r["receipt_no"]).split("-")[-1].zfill(4), font=font(38,True), fill=maroon)
    date=(r.get("paid_at") or r.get("created_at") or "")
    try: date=datetime.fromisoformat(str(date)).strftime("%d / %m / %Y")
    except Exception: date=str(date)[:10]
    d.text((560,318), date, font=font(27,False), fill=dark)
    d.text((500,394), str(r["name"])[:42], font=font(25,False), fill=dark)
    draw_wrapped(d,r["address"],(500,454),570,font(23,False),dark,5)
    d.text((500,613), str(r["phone"]), font=font(25,False), fill=dark)
    d.text((500,677), f"₹ {float(r['amount']):,.0f}", font=font(26,True), fill=dark)
    modes={"Cash":(585,752),"UPI":(764,752),"Google Pay":(764,752),"PhonePe":(764,752),"Other":(935,752)}
    if r.get("mode") in modes:
        x,y=modes[r["mode"]]; d.text((x,y),"✓",font=font(30,True),fill=maroon)
    return img


def receipt_pdf(r):
    img=receipt_image(r)
    buf=io.BytesIO(); img.save(buf,format="PNG"); buf.seek(0)
    pdf=io.BytesIO(); w,h=1536,1024
    c=canvas.Canvas(pdf,pagesize=(w,h))
    c.drawImage(ImageReader(buf),0,0,width=w,height=h,mask='auto')
    c.showPage(); c.save(); pdf.seek(0)
    return pdf.getvalue()


def receipt_url(r):
    base=os.getenv("APP_URL","").strip().rstrip("/")
    return f"{base}/?receipt={quote(str(r['receipt_no']))}" if base else ""

def sms_message(r):
    url=receipt_url(r)
    msg=(f"EKA DHANTHAYA MANDAP - ESTD. 2016\nChandha payment received successfully.\nName: {r['name']}\nAmount: Rs. {float(r['amount']):.0f}\nReceipt No: {r['receipt_no']}\nPayment: {r['mode']}\n")
    if url: msg+=f"View / Download Receipt: {url}\n"
    return msg+"Thank you for your contribution.\nGanapati Bappa Morya"

def sms_link(r,label="📱 SEND SMS"):
    phone="91"+str(r["phone"]).strip(); body=quote(sms_message(r))
    return f'<a href="sms:{phone}?body={body}" style="display:inline-block;padding:10px 14px;background:#F57C00;color:white;text-decoration:none;border-radius:10px;font-weight:700;margin:3px 0;">{label}</a>'

def receipt_card(r):
    img=receipt_image(r)
    st.image(img,use_container_width=True)
    st.download_button("🧾 Download Receipt PDF",receipt_pdf(r),f"{r['receipt_no']}.pdf","application/pdf",use_container_width=True)


def login():
    st.markdown('<div class="login-wrap"><div class="login-om">🕉️</div><div class="login-title">EKA DHANTHAYA MANDAP</div><div class="login-sub">Virtual Chandha • ESTD. 2016</div></div>',unsafe_allow_html=True)
    with st.form("login"):
        u=st.text_input("Username",placeholder="Enter username"); p=st.text_input("Password",type="password",placeholder="Enter password")
        ok=st.form_submit_button("🔐 LOGIN",use_container_width=True)
    if ok:
        if u.strip()==ADMIN_USERNAME and p==ADMIN_PASSWORD: st.session_state.auth=True; st.rerun()
        else: st.error("Invalid username or password.")

if "auth" not in st.session_state: st.session_state.auth=False
if not st.session_state.auth:
    receipt_no=st.query_params.get("receipt")
    if receipt_no:
        ensure_cloud_database(); r=get_donor_by_receipt(receipt_no)
        if r:
            st.markdown('<div style="text-align:center;padding:12px 0"><div style="font-size:42px">🕉️</div><h1 style="color:#8A3B00">EKA DHANTHAYA MANDAP</h1><p style="color:#7A5B32;font-weight:700">Official Chandha Receipt</p></div>',unsafe_allow_html=True)
            receipt_card(r); st.stop()
        st.error("Receipt not found or payment is not yet confirmed."); st.stop()
    login(); st.stop()

ensure_cloud_database()
st.sidebar.success("☁️ Cloud database connected")
st.sidebar.markdown('<div style="text-align:center;padding:8px 0 18px"><div style="font-size:46px">🕉️</div><div style="font-size:20px;font-weight:800;color:#8A3B00">EKA DHANTHAYA</div><div style="font-size:16px;font-weight:700;color:#A45A00">MANDAP</div><div style="font-size:12px;color:#7A5B32">ESTD. 2016</div></div>',unsafe_allow_html=True)
page=st.sidebar.radio("MENU",["🏠 Dashboard","➕ Add Chandha","✅ Paid Members","⏳ Pending Members","🧾 Receipts"])
if st.sidebar.button("🚪 Logout",use_container_width=True): st.session_state.auth=False; st.rerun()
st.markdown('<div class="hero"><div class="om">🕉️</div><h1>EKA DHANTHAYA MANDAP</h1><p>Virtual Chandha Management • ESTD. 2016</p></div>',unsafe_allow_html=True)

if page=="🏠 Dashboard":
    rows=get_donors(); paid=[r for r in rows if r["status"]=="Paid"]; pending=[r for r in rows if r["status"]=="Not Paid"]
    st.markdown('<div class="section-title">🙏 Chandha Dashboard</div>',unsafe_allow_html=True)
    c=st.columns(4)
    for col,(label,value) in zip(c,[("👥 Total Members",len(rows)),("✅ Paid Members",len(paid)),("⏳ Pending Members",len(pending)),("💰 Total Collection",f"₹{sum(r['amount'] for r in paid):,.0f}")]):
        col.markdown(f'<div class="metric"><div class="label">{label}</div><div class="value">{value}</div></div>',unsafe_allow_html=True)

elif page=="➕ Add Chandha":
    st.markdown('<div class="section-title">➕ Add Chandha</div>',unsafe_allow_html=True)
    with st.form("add"):
        c1,c2=st.columns(2)
        with c1:
            name=st.text_input("Name *"); phone=st.text_input("Phone Number *",placeholder="10-digit mobile number"); amount=st.number_input("Amount (₹) *",min_value=1.0,step=50.0)
        with c2:
            address=st.text_area("Address *",height=122); mode=st.selectbox("Mode of Payment",["Cash","UPI","Google Pay","PhonePe","Other"])
        status=st.radio("Payment Status",["Paid","Not Paid"],horizontal=True); submit=st.form_submit_button("🙏 SAVE CHANDHA",use_container_width=True)
    if submit:
        if not name.strip() or not phone.strip() or not address.strip() or amount<=0: st.error("Please fill Name, Phone Number, Address and Amount.")
        elif not phone.strip().isdigit() or len(phone.strip())!=10: st.error("Please enter a valid 10-digit Indian mobile number.")
        else:
            try:r=save_donor(name,address,phone,amount,mode,status)
            except Exception as e: st.error(f"Could not save donor: {e}"); st.stop()
            if status=="Paid":
                st.success(f"✅ Payment recorded. Receipt {r['receipt_no']} is ready.")
                st.image(receipt_image(r),use_container_width=True)
                st.download_button("🧾 Download Receipt PDF",receipt_pdf(r),f"{r['receipt_no']}.pdf","application/pdf",use_container_width=True)
                st.markdown(sms_link(r),unsafe_allow_html=True)
                st.caption("SMS opens your phone's Messages app with the receipt message prepared.")
            else: st.warning("⏳ Saved to Pending Members.")

elif page in ["✅ Paid Members","⏳ Pending Members"]:
    is_pending=page.startswith("⏳"); st.markdown(f'<div class="section-title">{"⏳ Pending Members" if is_pending else "✅ Paid Members"}</div>',unsafe_allow_html=True)
    search=st.text_input("🔎 Search by name or phone",placeholder="Type a name or phone number..."); rows=get_donors("Not Paid" if is_pending else "Paid"); shown=0
    for r in rows:
        if search and search.lower() not in (r["name"]+" "+r["phone"]).lower(): continue
        shown+=1
        with st.container(border=True):
            cols=st.columns([3,2,1.4,1.4,2])
            cols[0].markdown(f"**{r['name']}**  \n📍 {r['address']}"); cols[1].markdown(f"📞 **{r['phone']}**"); cols[2].markdown(f"💰 **₹{r['amount']:,.0f}**"); cols[3].markdown(f"**{r['mode']}**")
            if is_pending:
                if cols[4].button("✅ MARK PAID",key=f"pay{r['id']}"):
                    try: mark_paid(r["id"]); st.success(f"{r['name']} marked as paid. Receipt {r['receipt_no']} generated."); st.rerun()
                    except Exception as e: st.error(f"Could not update payment: {e}")
            else:
                st.image(receipt_image(r),use_container_width=True)
                a,b=st.columns(2)
                with a: st.download_button("🧾 RECEIPT PDF",receipt_pdf(r),f"{r['receipt_no']}.pdf","application/pdf",key=f"rec{r['id']}",use_container_width=True)
                with b: st.markdown(sms_link(r),unsafe_allow_html=True)
    if shown==0: st.info("No members found.")

elif page=="🧾 Receipts":
    st.markdown('<div class="section-title">🧾 Receipts</div>',unsafe_allow_html=True)
    q=st.text_input("🔎 Search receipt / name / phone",placeholder="EDM-2026-00001"); rows=get_donors("Paid"); shown=0
    for r in rows:
        if q and q.lower() not in (r["receipt_no"]+" "+r["name"]+" "+r["phone"]).lower(): continue
        shown+=1
        st.image(receipt_image(r),use_container_width=True)
        a,b=st.columns(2)
        with a: st.download_button("⬇️ Receipt PDF",receipt_pdf(r),f"{r['receipt_no']}.pdf","application/pdf",key=f"d{r['id']}",use_container_width=True)
        with b: st.markdown(sms_link(r),unsafe_allow_html=True)
    if shown==0: st.info("No receipts found.")

st.markdown('<div style="text-align:center;padding:30px 0 8px;color:#8A6A3B;font-size:12px">🙏 Ganapati Bappa Moriya • EKA DHANTHAYA MANDAP • ESTD. 2016 🙏</div>',unsafe_allow_html=True)
