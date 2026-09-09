import os
import re
import streamlit as st
import pandas as pd
from groq import Groq
import The_Database as db

# ================= PAGE CONFIG & STYLING =================
st.set_page_config(
    page_title="Seed2Harvest Enterprise",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Enterprise Agricultural Theme CSS
st.markdown("""
<style>
    /* Global Base */
    .main { background-color: #F8FAF8; }
    .stAppHeader { background-color: transparent; }
    
    /* Typography & Core Elements */
    h1, h2, h3, h4, h5, h6 { color: #1E3F20 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #1E3F20 0%, #2C5E30 100%);
        padding: 32px;
        border-radius: 8px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .hero-banner h1 { color: #FFFFFF !important; margin: 0; font-size: 2.4rem; font-weight: 600; letter-spacing: -0.5px; }
    .hero-banner p { color: #E8F5E9; margin: 8px 0 0 0; font-size: 1.1rem; font-weight: 300; }
    
    /* Image Showcase/Carousel */
    .image-showcase {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    
    /* Cards & Metrics */
    .metric-card {
        background: #FFFFFF;
        padding: 20px;
        border-radius: 8px;
        border-left: 4px solid #2C5E30;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 16px;
    }
    .metric-card h4 { margin-top: 0; font-size: 1.1rem; color: #1E3F20; }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E0E0E0;
    }
    .sidebar-title { color: #1E3F20; font-weight: 600; font-size: 1.2rem; margin-bottom: 16px; }
    
    /* Badges */
    .badge-popia {
        display: inline-block;
        background-color: #E8F5E9;
        color: #1E3F20;
        padding: 6px 12px;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 600;
        border: 1px solid #C8E6C9;
        margin-top: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database tables
db.init_db()

# ================= APPLICATION MIDDLEWARE =================
class AgriculturalMiddleware:
    """
    EA Application Layer: Input Boundary Guardrail & Dialect Normalization
    """
    AGRICULTURAL_KEYWORDS = [
        "soil", "plant", "crop", "fertilizer", "fertiliser", "seed", "harvest", 
        "pest", "leaf", "growth", "water", "yield", "nutrient", "fungus", 
        "nitrogen", "ph", "carbon", "dosage", "order", "price", "stock",
        "bioboost", "hydrocache", "nitro", "bioshield", "ecocert"
    ]
    
    # Regional Vernacular & South African Farming Slang Dictionary
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
    def enforce_domain_boundary(cls, text: str) -> bool:
        clean = text.lower()
        if any(w in clean for w in ["hello", "hi", "help", "order", "quote", "buy"]):
            return True
        return any(keyword in clean for keyword in cls.AGRICULTURAL_KEYWORDS)

    @classmethod
    def normalize_vernacular(cls, text: str) -> tuple[str, list[str]]:
        normalized = text
        detected = []
        for pattern, replacement in cls.SLANG_DICTIONARY.items():
            if re.search(pattern, normalized, re.IGNORECASE):
                detected.append(pattern.replace(r"\b", ""))
                normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        return normalized, detected

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
You are the Seed2Harvest Agricultural Technical Consultant and Sales AI Agent.
SMME Partner: Shaun Cairns (Seed2Harvest, Cape Town, South Africa).

STRICT BOUNDARY CONSTRAINTS:
1. Ground your advice exclusively in Seed2Harvest's certified product catalog and verified organic agronomy:
{catalog_context}
2. Never invent unverified chemical formulations or excessive dosages. Respect ECOCERT safety limits.
3. If a farmer asks for chemical remedies that harm biological soil life, gently steer them toward our organic biological alternatives.
4. When a farmer indicates intent to purchase, guide them clearly on the exact quantity and unit price.
5. Tone: Professional, respectful, practical, supportive of commercial and smallholder farmers. Keep responses concise. Do not use emojis.
"""

# ================= SIDEBAR & NAVIGATION =================
with st.sidebar:
    st.markdown("<div class='sidebar-title'>Seed2Harvest Systems</div>", unsafe_allow_html=True)
    st.markdown("### Enterprise Architecture")
    st.markdown("""
    **Business Layer**  
    Mitigates manual response churn via automated technical advisory and lead qualification.
    
    **Application Layer**  
    Python middleware executing domain filters and dialect translation before API dispatch.
    
    **Data Layer**  
    Relational SQLite schema (`orders`, `inventory`, `clients`) enforcing referential integrity.
    
    **Technology Layer**  
    Python 3.11, Linux PaaS, and LPU inference hardware.
    """)
    st.markdown('<div class="badge-popia">POPIA Act Compliant</div>', unsafe_allow_html=True)
    
    st.divider()
    st.caption("Version 2.1.0 | Operational Value Stream Module")

# ================= MAIN UI LAYOUT =================
st.markdown("""
<div class="hero-banner">
    <h1>Seed2Harvest Enterprise Consultant</h1>
    <p>Operational Value Stream: Soil Nutrition, Vernacular Guidance & Real-time Stock Reservation</p>
</div>
""", unsafe_allow_html=True)

# Image Showcase (Gallery replacing the need for a third-party carousel package)
st.markdown("#### Agricultural Operations")
col_img1, col_img2, col_img3 = st.columns(3)
try:
    # Utilizing the images referenced from the project zip directory
    with col_img1:
        st.image("images/clare-tallamy-pXIlqK9fas8-unsplash.jpg", use_container_width=True, caption="Biological Crop Care")
    with col_img2:
        st.image("images/maxresdefault.jpg", use_container_width=True, caption="Field Operations")
    with col_img3:
        st.image("images/x91000-r4x000619_rrd.avif", use_container_width=True, caption="Precision Agriculture")
except Exception:
    st.info("Image assets pending deployment in /images directory.")

st.divider()

# Main Application Tabs (Removed Emojis)
tab_chat, tab_catalog, tab_order = st.tabs([
    "Technical Advisory", 
    "Live Inventory", 
    "Reserve Order"
])

# ----------------- TAB 1: ADVISORY CHAT -----------------
with tab_chat:
    st.markdown("##### Enterprise AI Consultation")
    st.caption("Active Guardrails: Domain Boundary Enforcement & South African Dialect Interpretation.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Welcome to Seed2Harvest. How can I assist you with your soil nutrition, biological crop care, or produce orders today?"}
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_prompt := st.chat_input("Query soil treatments, pest management, or pricing..."):
        with st.chat_message("user"):
            st.markdown(user_prompt)
        st.session_state.messages.append({"role": "user", "content": user_prompt})

        # Step 1: Middleware Domain Boundary Inspection
        if not AgriculturalMiddleware.enforce_domain_boundary(user_prompt):
            disclaimer = (
                "**Out of Domain Scope:** I am bounded specifically to assist with Seed2Harvest's agricultural products, "
                "soil biology, and order reservations. Please query an agronomic or product-related topic."
            )
            with st.chat_message("assistant"):
                st.warning(disclaimer, icon=None)
            st.session_state.messages.append({"role": "assistant", "content": disclaimer})
        else:
            # Step 2: Vernacular Normalization
            normalized_prompt, detected_terms = AgriculturalMiddleware.normalize_vernacular(user_prompt)
            
            if detected_terms:
                st.toast(f"Semantic Interpreter: Mapped dialect terms [{', '.join(detected_terms)}]", icon=None)

            # Step 3: Groq LLM Inference Call
            if not groq_client:
                st.error("API Key not detected. Please configure system environment variables.")
            else:
                try:
                    chat_completion = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": f"Farmer Query (Normalized): {normalized_prompt}"}
                        ],
                        temperature=0.15, # Highly conservative to prevent hallucination
                        max_tokens=450
                    )
                    reply = chat_completion.choices[0].message.content
                    with st.chat_message("assistant"):
                        st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                except Exception as err:
                    st.error(f"Inference Engine Error: {err}")

# ----------------- TAB 2: LIVE CATALOG -----------------
with tab_catalog:
    st.markdown("##### Warehouse Stock (Relational Store)")
    st.caption("Direct integration with `inventory_master` via indexed SQL queries.")
    
    current_inventory = db.fetch_inventory()
    df_catalog = pd.DataFrame(
        current_inventory, 
        columns=["Product Name", "Category", "Available Stock", "Unit Price (ZAR)", "Dosage & Application Guideline"]
    )
    df_catalog["Unit Price (ZAR)"] = df_catalog["Unit Price (ZAR)"].map("R {:,.2f}".format)
    st.dataframe(df_catalog, use_container_width=True, hide_index=True)

# ----------------- TAB 3: ORDER COMMITMENT -----------------
with tab_order:
    st.markdown("##### Stock Locking & Order Reservation")
    st.caption("Executes atomic SQL transactions with PII isolation.")
    
    col1, col2 = st.columns(2)
    with col1:
        client_name = st.text_input("Farmer / Organization Name")
        client_phone = st.text_input("Phone Number")
        client_location = st.text_input("Delivery District (e.g., Paarl, Western Cape)")
    
    with col2:
        product_names = [p[0] for p in current_inventory]
        selected_product = st.selectbox("Select Certified Product", product_names)
        order_qty = st.number_input("Quantity", min_value=1, max_value=500, value=5, step=1)
        popia_consent = st.checkbox("I consent to Seed2Harvest storing my contact info strictly for delivery processing.")

    if st.button("Commit Order Reservation", type="primary"):
        if not client_name or not client_phone or not client_location:
            st.error("Please provide all required organization information.", icon=None)
        elif not popia_consent:
            st.warning("Data privacy consent is mandatory to process order allocations.", icon=None)
        else:
            success, result = db.process_order_transaction(
                farmer_name=client_name,
                phone=client_phone,
                location=client_location,
                product_name=selected_product,
                quantity=order_qty
            )
            if success:
                st.success("Order Reservation successfully committed to the database.", icon=None)
                st.markdown(f"""
                <div class="metric-card">
                    <h4>Receipt Reference: ORD-00{result['order_id']}</h4>
                    <p><strong>Allocated Item:</strong> {result['product']} &times; {result['quantity']}</p>
                    <p><strong>Total Amount Due:</strong> R {result['total_cost']:,.2f}</p>
                    <p><strong>Warehouse Status:</strong> Inventory Reserved. Remaining Stock: {result['remaining_stock']} units.</p>
                </div>
                """, unsafe_allow_html=True)
                st.rerun()
            else:
                st.error(f"Transaction Aborted: {result}", icon=None)
