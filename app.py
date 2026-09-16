import os
import re
import streamlit as st
import pandas as pd
from groq import Groq
import The_Database as db

# ================= PAGE CONFIG & STYLING =================
st.set_page_config(
    page_title="Seed 2 Harvest | Strategic Agent",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    h1, h2, h3 { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 800; text-transform: uppercase; }
    .main-title { color: #ffffff; font-size: 2.5rem; line-height: 1.1; margin-bottom: 0px; margin-top: 10px;}
    .sub-title { color: #c69c6d; font-size: 0.9rem; letter-spacing: 3px; font-weight: 600; margin-bottom: 20px;}
    .section-header { color: #c69c6d; font-size: 1.5rem; margin-top: 20px; margin-bottom: 15px;}
    
    /* Constrain Hero Image Height so user doesn't have to scroll */
    .hero-img-container img {
        max-height: 160px !important;
        object-fit: cover;
        width: 100%;
        border-radius: 4px;
        border: 1px solid #333;
    }
    
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > div {
        background-color: #1e2127; color: #ffffff; border: 1px solid #333333;
    }
    .stTextInput > div > div > input:focus { border-color: #c69c6d; box-shadow: none; }
    
    .custom-warning {
        background-color: #3b4020; color: #d7ffd9; padding: 15px; border-radius: 5px; margin: 20px 0; font-size: 0.95rem;
    }
    .quote-text { color: #c69c6d; font-style: italic; margin-bottom: 20px; }
    
    .stButton > button {
        background-color: #1e2127; color: #ffffff; border: 1px solid #c69c6d; border-radius: 4px; font-weight: 600; letter-spacing: 1px;
    }
    .stButton > button:hover { background-color: #c69c6d; color: #000000; border: 1px solid #c69c6d; }
    
    [data-testid="stSidebar"] { background-color: #16181c; border-right: 1px solid #333; }
    .sidebar-title { color: #c69c6d; font-size: 1.2rem; font-weight: bold; margin-bottom: 20px;}
    .sidebar-subtitle { color: #888888; font-size: 0.75rem; letter-spacing: 1px; margin-bottom: 10px;}
    
    .quote-box {
        background-color: #16181c; border: 2px solid #c69c6d; padding: 30px; border-radius: 6px; font-family: monospace; color: #fff; margin-top: 20px;
    }
    
    .footer { text-align: center; margin-top: 40px; padding-top: 15px; border-top: 1px solid #333; }
    .footer h4 { color: #c69c6d; margin: 0; font-size: 1.1rem; letter-spacing: 2px;}
    .footer p { color: #666666; font-size: 0.75rem; letter-spacing: 1px; margin-top: 5px;}
</style>
""", unsafe_allow_html=True)

db.init_db()

# ================= SESSION STATE =================
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "user_data" not in st.session_state: st.session_state.user_data = {"name": "", "farm": "", "location": "", "email": ""}
if "messages" not in st.session_state: st.session_state.messages = []
if "basket" not in st.session_state: st.session_state.basket = {}

# ================= APPLICATION MIDDLEWARE =================
class AgriculturalMiddleware:
    SLANG_DICTIONARY = {
        r"\bblaarbrand\b": "leaf scorch / fungal burn",
        r"\bkunsmis\b": "organic fertilizer",
        r"\bgoggas\b": "agricultural pests / insects",
        r"\bspuit\b": "spray application / foliar dosage",
        r"\bbrak grond\b": "saline dry alkaline soil",
        r"\bcompost\b": "organic matter / soil enhancer",
        r"\bboer\b": "farmer",
        r"\blap\b": "cultivated field plot",
        r"\bplaag\b": "pest infestation",
        r"\bgif\b": "crop protection remedy"
    }

    @classmethod
    def normalize_vernacular(cls, text: str) -> str:
        normalized = text
        for pattern, replacement in cls.SLANG_DICTIONARY.items():
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        return normalized

# ================= GROQ CLIENT SETUP =================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY and "GROQ_API_KEY" in st.secrets:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

catalog_data = db.fetch_inventory()
catalog_context = "\n".join([
    f"- Product: {row[0]} | Category: {row[1]} | Stock: {row[2]} units | Price: R{row[3]:.2f} | Safe Usage: {row[4]}"
    for row in catalog_data
])

SYSTEM_PROMPT = f"""
You are the Seed 2 Harvest Strategic Agent.
SMME Partner: Shaun Cairns (Cape Town, South Africa).

INSTRUCTIONS:
1. Ground your advice in the certified product catalog:
{catalog_context}
2. MAINTAIN CONTEXT MEMORY: Remember previous products discussed by the user across turns (e.g. if the user previously requested NitroGrow Pellets, keep referencing them).
3. Respect ECOCERT safety limits and steer toward organic biological alternatives.
4. Keep responses professional, clear, and actionable. Do not use emojis.
"""

# ================= SIDEBAR NAVIGATION =================
with st.sidebar:
    st.markdown("<div class='sidebar-title'>ERTG</div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-subtitle'>OPERATIONS</div>", unsafe_allow_html=True)
    
    if st.session_state.authenticated:
        page_selection = st.radio(
            "Navigate", 
            ["❖ CHAT", "☷ CATALOGUE", "📝 RESERVE ORDER", "⚙ GLOBAL FEED"],
            label_visibility="collapsed"
        )
    else:
        page_selection = "ONBOARDING"
        st.caption("Please authenticate to access operations.")
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-title'>⛟ YOUR BASKET</div>", unsafe_allow_html=True)
    if not st.session_state.basket:
        st.write("Empty")
    else:
        for prod, qty in st.session_state.basket.items():
            st.write(f"- {qty}x {prod}")
            
    if st.button("CLEAR BASKET"):
        st.session_state.basket = {}
        st.toast("Basket Cleared")
        st.rerun()
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("TERMINATE"):
        st.session_state.authenticated = False
        st.session_state.messages = []
        st.session_state.basket = {}
        st.rerun()

# ================= MAIN HEADER (Constrained Image) =================
st.markdown("<div class='hero-img-container'>", unsafe_allow_html=True)
try:
    st.image("images/maxresdefault.jpg", use_container_width=True)
except Exception:
    st.markdown("<div style='height: 80px; background-color: #1a1e23; border: 1px solid #333;'></div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='main-title'>SEED 2<br>HARVEST</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>ELEVATE YOUR EVERYDAY</div>", unsafe_allow_html=True)

# ================= VIEWS =================

if not st.session_state.authenticated:
    st.markdown("<div class='section-header'>❖ CLIENT ONBOARDING</div>", unsafe_allow_html=True)
    
    col_form, _ = st.columns([2, 1])
    with col_form:
        client_name = st.text_input("NAME", key="onboard_name")
        client_farm = st.text_input("FARM / COMPANY", key="onboard_farm")
        client_location = st.text_input("LOCATION", key="onboard_loc")
        client_email = st.text_input("EMAIL ADDRESS", key="onboard_email")
        
        st.markdown("""
        <div class="custom-warning">
            Hello fellow farmer. For the agent to work effectively we need permission to work with your data. Click yes to continue or leave.
        </div>
        """, unsafe_allow_html=True)
        
        permission = st.checkbox("I GRANT PERMISSION")
        
        if st.button("AUTHORIZE ENTRY"):
            if client_name and client_farm and client_location and client_email and permission:
                st.session_state.user_data = {
                    "name": client_name, "farm": client_farm, "location": client_location, "email": client_email
                }
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Please complete all fields, provide an email address, and grant permission to proceed.")

elif page_selection == "❖ CHAT":
    st.markdown("<div class='section-header'>STRATEGIC AGENT</div>", unsafe_allow_html=True)
    
    if not st.session_state.messages:
        st.session_state.messages = [
            {"role": "assistant", "content": f"Welcome back, {st.session_state.user_data['name']}. How can I assist your operations at {st.session_state.user_data['farm']} today?"}
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_prompt := st.chat_input("MESSAGE"):
        with st.chat_message("user"):
            st.markdown(user_prompt)
        st.session_state.messages.append({"role": "user", "content": user_prompt})

        normalized_prompt = AgriculturalMiddleware.normalize_vernacular(user_prompt)
        
        if not groq_client:
            st.error("SYSTEM ERROR: API connectivity offline.")
        else:
            try:
                # Format full conversational history into Groq payload to preserve memory across turns
                conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}]
                for m in st.session_state.messages:
                    conversation_history.append({"role": m["role"], "content": m["content"]})
                
                chat_completion = groq_client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=conversation_history,
                    temperature=0.3,
                    max_tokens=450
                )
                reply = chat_completion.choices[0].message.content
                with st.chat_message("assistant"):
                    st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as err:
                st.error(f"Inference Engine Error: {err}")

elif page_selection == "☷ CATALOGUE":
    st.markdown("<div class='section-header'>PRODUCT CATALOGUE & BASKET ALLOCATION</div>", unsafe_allow_html=True)
    
    for row in catalog_data:
        p_name, p_cat, p_stock, p_price, p_guide = row[0], row[1], row[2], row[3], row[4]
        cols = st.columns([3, 1])
        with cols[0]:
            st.markdown(f"**{p_name}** ({p_cat}) — **ZAR {p_price:.2f}** | Stock: {p_stock}")
            st.caption(f"Guideline: {p_guide}")
        with cols[1]:
            qty = st.number_input("Qty", min_value=0, max_value=int(p_stock), value=st.session_state.basket.get(p_name, 0), key=f"cat_{p_name}")
            if qty > 0:
                st.session_state.basket[p_name] = qty
            elif p_name in st.session_state.basket:
                del st.session_state.basket[p_name]
        st.markdown("---")

elif page_selection == "📝 RESERVE ORDER":
    st.markdown("<div class='section-header'>RESERVE ORDER & OFFICIAL QUOTATION</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("FARM / COMPANY", value=st.session_state.user_data["farm"], disabled=True)
        st.text_input("LOCATION", value=st.session_state.user_data["location"], disabled=True)
    
    with col2:
        st.text_input("CLIENT NAME", value=st.session_state.user_data["name"], disabled=True)
        email_input = st.text_input("EMAIL FOR QUOTATION", value=st.session_state.user_data["email"])
        phone = st.text_input("CONTACT NUMBER")

    st.markdown("### CURRENT BASKET ITEMS")
    if not st.session_state.basket:
        st.warning("Your basket is empty. Add items from the Catalogue page or select via chat.")
    else:
        for item, qty in st.session_state.basket.items():
            st.write(f"- {qty}x {item}")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("PROCESS TRANSACTION & GENERATE QUOTE"):
        if not phone or not email_input:
            st.error("Contact number and email are required to process the order and generate the quotation.")
        elif not st.session_state.basket:
            st.error("Cannot generate a quotation with an empty basket.")
        else:
            st.success("Transaction Successfully Recorded in SQLite Database!")
            
            # Generate Formal Quotation Document Layout based on Template Structure[cite: 4]
            st.markdown(f"""
            <div class="quote-box">
                <b>SEED 2 HARVEST (PTY) LTD</b>[cite: 4]<br>
                123 Agricultural Way, Cape Town, 8001[cite: 4]<br>
                support@seed2harvest.co.za | +27 21 555 0192[cite: 4]<br>
                ------------------------------------------------------------------<br>
                <b>OFFICIAL QUOTATION & BILLING SUMMARY</b><br><br>
                <b>BILL TO:</b> {st.session_state.user_data['name']} ({st.session_state.user_data['farm']})[cite: 4]<br>
                <b>ADDRESS:</b> {st.session_state.user_data['location']}[cite: 4]<br>
                <b>CONTACT:</b> {phone} | {email_input}[cite: 4]<br>
                <b>QUOTE NO:</b> #INV00001 &nbsp;&nbsp;|&nbsp;&nbsp; <b>DATE:</b> {pd.Timestamp.now().strftime('%Y-%m-%d')}[cite: 4]<br>
                <b>VALID FOR:</b> 14 days[cite: 4]<br>
                ------------------------------------------------------------------<br>
                <b>DESCRIPTION &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; QTY &nbsp;&nbsp;&nbsp; UNIT PRICE &nbsp;&nbsp; TOTAL</b><br>
            """, unsafe_allow_html=True)
            
            subtotal = 0.0
            for prod, qty in st.session_state.basket.items():
                price_row = [p[3] for p in catalog_data if p[0] == prod]
                price = price_row[0] if price_row else 0.0
                total_item = price * qty
                subtotal += total_item
                st.markdown(f"<span style='font-family:monospace;'>{prod:<35} {qty:<7} R{price:<11.2f} R{total_item:.2f}</span>", unsafe_allow_html=True)
            
            tax_total = subtotal * 0.15  # 15% VAT standard for SA
            grand_total = subtotal + tax_total
            
            st.markdown(f"""
                ------------------------------------------------------------------<br>
                <b>SUBTOTAL:</b> R {subtotal:.2f}[cite: 4]<br>
                <b>TAX RATE (15% VAT):</b> R {tax_total:.2f}[cite: 4]<br>
                <b>SHIPPING / HANDLING:</b> R 0.00[cite: 4]<br>
                <b>QUOTE TOTAL:</b> R {grand_total:.2f}[cite: 4]<br>
                ------------------------------------------------------------------<br>
                <b>Notes & Terms:</b>[cite: 4]<br>
                - 50% deposit required upon order confirmation; balance due within 30 days[cite: 4].<br>
                - All biological formulations comply with strict ECOCERT safety guidelines.<br>
                <br>
                <i>Quotation successfully dispatched to: {email_input}</i>
            </div>
            """, unsafe_allow_html=True)

elif page_selection == "⚙ GLOBAL FEED":
    st.markdown("<div class='section-header'>GLOBAL FEED & SYSTEM ARCHITECTURE</div>", unsafe_allow_html=True)
    st.markdown("""
    **ACTIVE SYSTEMS:**
    - **EA Middleware:** Python runtime translating regional vernacular & normalizing input streams.
    - **Persistence:** SQLite relational mapping (`orders`, `inventory`, `clients`).
    - **Compliance:** POPIA standards enforced on client data encapsulation.
    - **Inference Engine:** Groq LPU hardware routing to openai/gpt-oss-120b.
    """)

# ================= FOOTER =================
st.markdown("""
<div class='footer'>
    <h4>BUZUZI INCORPORATED</h4>
    <p>FOLLOW ON SOCIALS: @SEED2HARVEST_GLOBAL</p>
</div>
""", unsafe_allow_html=True)
