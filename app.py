import os
import re
import streamlit as st
import pandas as pd
from groq import Groq
import The_Database as db

# ================= PAGE CONFIG & STYLING =================
st.set_page_config(
    page_title="Seed2Harvest | Enterprise AI Consultant",
    page_icon="🌱",
    layout="wide"
)

# Custom Enterprise Agricultural Theme CSS
st.markdown("""
<style>
    .main { background-color: #f7f9f6; }
    .stAppHeader { background-color: transparent; }
    .hero-banner {
        background: linear-gradient(135deg, #1b4d3e 0%, #2e7d32 100%);
        padding: 24px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
    }
    .hero-banner h1 { color: #ffffff !important; margin: 0; font-size: 2.2rem; }
    .hero-banner p { color: #d7ffd9; margin: 6px 0 0 0; font-size: 1.05rem; }
    .metric-card {
        background: white;
        padding: 16px;
        border-radius: 8px;
        border-left: 5px solid #2e7d32;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 12px;
    }
    .badge-popia {
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 4px 10px;
        border-radius: 14px;
        font-size: 0.82rem;
        font-weight: 600;
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
        """Returns True if input is strictly relevant to agriculture/order workflows."""
        clean = text.lower()
        # Allow transactional or conversational greetings
        if any(w in clean for w in ["hello", "hi", "help", "order", "quote", "buy"]):
            return True
        return any(keyword in clean for keyword in cls.AGRICULTURAL_KEYWORDS)

    @classmethod
    def normalize_vernacular(cls, text: str) -> tuple[str, list[str]]:
        """Maps colloquial phrases into standardized agronomic language."""
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

# Fetch inventory catalog context for LLM Grounding
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
5. Tone: Respectful, practical, supportive of commercial and smallholder farmers. Keep responses concise and action-oriented.
"""

# ================= UI LAYOUT =================
st.markdown("""
<div class="hero-banner">
    <h1>🌱 Seed2Harvest Enterprise AI Consultant</h1>
    <p>Operational Value Stream Assistant: Soil Nutrition, Vernacular Guidance & Real-time Stock Reservation</p>
</div>
""", unsafe_allow_html=True)

# Main Application Tabs
tab_chat, tab_catalog, tab_order, tab_admin = st.tabs([
    "💬 Technical Advisory Chat", 
    "📦 Real-Time Inventory", 
    "📝 Reserve Order", 
    "⚙️ Architecture & POPIA Info"
])

# ----------------- TAB 1: ADVISORY CHAT -----------------
with tab_chat:
    st.markdown("##### Consult with the Agricultural AI Agent")
    st.caption("Includes real-time domain boundary guardrails and South African dialect interpretation.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Goeiedag! Welcome to Seed2Harvest. How can I assist you with your soil nutrition, biological crop care, or produce orders today?"}
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_prompt := st.chat_input("Ask about soil treatments, pest management, or pricing..."):
        # Display raw user input
        with st.chat_message("user"):
            st.markdown(user_prompt)
        st.session_state.messages.append({"role": "user", "content": user_prompt})

        # Step 1: Middleware Domain Boundary Inspection
        if not AgriculturalMiddleware.enforce_domain_boundary(user_prompt):
            disclaimer = (
                "⚠️ **Out of Domain Scope:** I am bounded specifically to assist with Seed2Harvest's agricultural products, "
                "soil biology, and order reservations. Please query an agronomic or product-related topic."
            )
            with st.chat_message("assistant"):
                st.warning(disclaimer)
            st.session_state.messages.append({"role": "assistant", "content": disclaimer})
        else:
            # Step 2: Vernacular Normalization
            normalized_prompt, detected_terms = AgriculturalMiddleware.normalize_vernacular(user_prompt)
            
            if detected_terms:
                st.toast(f"Semantic Interpreter: Mapped dialect terms [{', '.join(detected_terms)}]", icon="🌐")

            # Step 3: Groq LLM Inference Call
            if not groq_client:
                st.error("Groq API Key not detected. Please configure `GROQ_API_KEY` in environment variables or Streamlit secrets.")
            else:
                try:
                    chat_completion = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": f"Farmer Query (Normalized): {normalized_prompt}"}
                        ],
                        temperature=0.2, # Conservative temperature to eliminate speculative hallucinations
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
    st.markdown("##### Current Warehouse Stock (Relational SQLite Store)")
    st.caption("Directly queries `inventory_master` using indexed transactional SQL.")
    
    current_inventory = db.fetch_inventory()
    df_catalog = pd.DataFrame(
        current_inventory, 
        columns=["Product Name", "Category", "Available Stock", "Unit Price (ZAR)", "Dosage & Application Guideline"]
    )
    df_catalog["Unit Price (ZAR)"] = df_catalog["Unit Price (ZAR)"].map("R {:,.2f}".format)
    st.dataframe(df_catalog, use_container_width=True, hide_index=True)

# ----------------- TAB 3: ORDER COMMITMENT -----------------
with tab_order:
    st.markdown("##### Lock Stock & Reserve Order")
    st.caption("Executes an atomic SQL write with POPIA client PII tokenization.")
    
    col1, col2 = st.columns(2)
    with col1:
        client_name = st.text_input("Farmer / Organization Name")
        client_phone = st.text_input("Phone Number")
        client_location = st.text_input("Delivery District / Farm Location (e.g., Paarl, Western Cape)")
    
    with col2:
        product_names = [p[0] for p in current_inventory]
        selected_product = st.selectbox("Select Certified Product", product_names)
        order_qty = st.number_input("Quantity", min_value=1, max_value=500, value=5, step=1)
        popia_consent = st.checkbox("I consent to Seed2Harvest storing my contact info strictly for delivery per POPIA regulations.")

    if st.button("Commit Order Reservation", type="primary"):
        if not client_name or not client_phone or not client_location:
            st.error("Please fill in all buyer information fields.")
        elif not popia_consent:
            st.warning("POPIA consent is mandatory to process and store order allocations.")
        else:
            success, result = db.process_order_transaction(
                farmer_name=client_name,
                phone=client_phone,
                location=client_location,
                product_name=selected_product,
                quantity=order_qty
            )
            if success:
                st.success("✅ Order Reservation Committed to Relational Database!")
                st.markdown(f"""
                <div class="metric-card">
                    <h4>Receipt Reference: #{result['order_id']}</h4>
                    <p><strong>Allocated Item:</strong> {result['product']} &times; {result['quantity']}</p>
                    <p><strong>Total Amount Due:</strong> R {result['total_cost']:,.2f}</p>
                    <p><strong>Warehouse Status:</strong> Inventory Reserved. Remaining Stock: {result['remaining_stock']} units.</p>
                </div>
                """, unsafe_allow_html=True)
                st.rerun()
            else:
                st.error(f"Transaction Aborted: {result}")

# ----------------- TAB 4: ARCHITECTURE & COMPLIANCE -----------------
with tab_admin:
    st.markdown("##### Enterprise Architecture & Regulatory Alignment")
    st.markdown("""
    * **Business Layer:** Aligns technical touchpoints directly with Shaun Cairns' core fulfillment bottleneck—mitigating manual response churn.
    * **Application Layer:** Streamlit UI + Python middleware executing domain filters and dialect translation before Groq API dispatch.
    * **Data Layer:** SQLite schema featuring relational referential integrity (`orders_commitment`, `inventory_master`, `popia_encrypted_clients`).
    * **Technology Layer:** Python 3.11 runtime, Linux container PaaS on Streamlit Community Cloud, and Groq LPU inference hardware.
    """)
    st.markdown('<span class="badge-popia">POPIA Act Compliant Architecture</span>', unsafe_allow_html=True)