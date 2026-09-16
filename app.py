
import streamlit as st
from datetime import datetime
from pathlib import Path
import sqlite3, hashlib, base64

APP_TITLE = "EKA DHANTHAYA MANDAP"
DB = "edm_chandha.db"
RECEIPT_DIR = Path("receipts")
RECEIPT_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title=APP_TITLE, page_icon="🕉️", layout="wide")

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

def db():
    con=sqlite3.connect(DB)
    con.row_factory=sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS donors(
        id INTEGER PRIMARY KEY AUTOINCREMENT, receipt_no TEXT, name TEXT,
        address TEXT, phone TEXT, amount REAL, mode TEXT, status TEXT,
        created_at TEXT, paid_at TEXT, whatsapp_sent INTEGER DEFAULT 0)""")
    con.commit()
    return con

def receipt_text(r):
    return f"""EKA DHANTHAYA MANDAP
ESTD. 2016
GANESH CHANDHA RECEIPT
--------------------------------
Receipt No: {r['receipt_no']}
Date: {r['paid_at'] or r['created_at']}
Name: {r['name']}
Phone: {r['phone']}
Address: {r['address']}
Amount: Rs. {r['amount']:.2f}
Payment Mode: {r['mode']}
--------------------------------
Thank you for your contribution.
GANAPATHI BAPPA MORIYA 🙏
"""

def login():
    st.markdown("<div class='login'>🕉️<h1>EKA DHANTHAYA MANDAP</h1><p>Virtual Chandha • ESTD. 2016</p></div>", unsafe_allow_html=True)
    with st.form("login"):
        u=st.text_input("Username")
        p=st.text_input("Password", type="password")
        ok=st.form_submit_button("LOGIN", use_container_width=True)
    if ok:
        if u=="EDM" and p=="Edm@2016":
            st.session_state.auth=True; st.rerun()
        else: st.error("Invalid username or password.")

if "auth" not in st.session_state: st.session_state.auth=False
st.markdown("""<style>
.stApp{background:linear-gradient(135deg,#120b05,#241307,#0d0a06);color:#fff}
h1,h2,h3{color:#f5c65d}.block-container{max-width:1200px}
.login{text-align:center;padding:50px 10px 20px}.login h1{margin-bottom:4px}
.card{background:#21150b;border:1px solid #8d6425;border-radius:16px;padding:18px}
div.stButton>button{border-radius:10px;border:1px solid #b8862c}
</style>""", unsafe_allow_html=True)

if not st.session_state.auth:
    login(); st.stop()

con=db()
st.sidebar.markdown("## 🕉️ EDM")
st.sidebar.caption("EKA DHANTHAYA MANDAP\nESTD. 2016")
page=st.sidebar.radio("Menu",["Dashboard","Add Chandha","Paid Members","Pending Members","Receipts"])
if st.sidebar.button("Logout"):
    st.session_state.auth=False; st.rerun()

if page=="Dashboard":
    rows=con.execute("SELECT * FROM donors").fetchall()
    paid=[r for r in rows if r["status"]=="Paid"]; pending=[r for r in rows if r["status"]=="Not Paid"]
    total=sum(r["amount"] for r in paid); pending_amt=sum(r["amount"] for r in pending)
    st.title("🕉️ Chandha Dashboard")
    c=st.columns(4)
    c[0].metric("Total Members",len(rows)); c[1].metric("Paid",len(paid))
    c[2].metric("Pending",len(pending)); c[3].metric("Collected",f"₹{total:,.0f}")
    st.info(f"Pending amount: ₹{pending_amt:,.0f}")
    st.caption("Simple local demo is ready. Configure Supabase + WhatsApp before public deployment.")

elif page=="Add Chandha":
    st.title("➕ Add Chandha")
    with st.form("add"):
        name=st.text_input("Name *"); phone=st.text_input("Phone Number *"); address=st.text_area("Address")
        amount=st.number_input("Amount (₹)",min_value=0.0,step=10.0)
        mode=st.selectbox("Mode of Payment",["Cash","UPI","Google Pay","PhonePe","Other"])
        status=st.radio("Status",["Paid","Not Paid"],horizontal=True)
        submit=st.form_submit_button("SAVE MEMBER",use_container_width=True)
    if submit:
        if not name or not phone or amount<=0: st.error("Name, phone and amount are required.")
        else:
            cur=con.execute("SELECT COUNT(*) FROM donors").fetchone()[0]+1
            receipt=f"EDM-2026-{cur:05d}"
            now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            paid_at=now if status=="Paid" else None
            con.execute("INSERT INTO donors(receipt_no,name,address,phone,amount,mode,status,created_at,paid_at) VALUES(?,?,?,?,?,?,?,?,?)",
                        (receipt,name,address,phone,amount,mode,status,now,paid_at)); con.commit()
            st.success(f"Saved successfully. Receipt: {receipt}" if status=="Paid" else "Saved in Pending Members.")
            if status=="Paid": st.download_button("🧾 Download Receipt",receipt_text(con.execute("SELECT * FROM donors ORDER BY id DESC LIMIT 1").fetchone()).encode(),"receipt.txt","text/plain")

elif page in ["Paid Members","Pending Members"]:
    is_pending=page.startswith("Pending")
    st.title("⏳ Pending Members" if is_pending else "✅ Paid Members")
    rows=con.execute("SELECT * FROM donors WHERE status=? ORDER BY id DESC",("Not Paid" if is_pending else "Paid",)).fetchall()
    search=st.text_input("Search name / phone")
    for r in rows:
        if search and search.lower() not in (r["name"]+" "+r["phone"]).lower(): continue
        with st.container(border=True):
            cols=st.columns([3,2,2,2,2])
            cols[0].write(f"**{r['name']}**\n\n{r['address']}")
            cols[1].write(f"📞 {r['phone']}")
            cols[2].write(f"💰 ₹{r['amount']:,.0f}\n\n{r['mode']}")
            cols[3].write(r["status"])
            if is_pending:
                if cols[4].button("MARK PAID",key=f"pay{r['id']}"):
                    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    con.execute("UPDATE donors SET status='Paid',paid_at=? WHERE id=?",(now,r["id"])); con.commit()
                    st.success(f"{r['name']} marked as paid. Receipt {r['receipt_no']} generated.")
                    st.rerun()
            else:
                txt=receipt_text(r).encode()
                cols[4].download_button("RECEIPT",txt,f"{r['receipt_no']}.txt","text/plain",key=f"rec{r['id']}")

elif page=="Receipts":
    st.title("🧾 Receipts")
    q=st.text_input("Search receipt / name / phone")
    rows=con.execute("SELECT * FROM donors WHERE status='Paid' ORDER BY id DESC").fetchall()
    for r in rows:
        if q and q.lower() not in (r["receipt_no"]+" "+r["name"]+" "+r["phone"]).lower(): continue
        st.write(f"**{r['receipt_no']}** — {r['name']} — ₹{r['amount']:,.0f} — {r['mode']}")
        st.download_button("Download",receipt_text(r).encode(),f"{r['receipt_no']}.txt","text/plain",key=f"d{r['id']}")
        st.divider()
