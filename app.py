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

# Dark Theme & Gold Accent CSS matching the original UI
st.markdown("""
<style>
    /* Force dark theme colors */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* Headers and Text */
    h1, h2, h3 {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 800;
        text-transform: uppercase;
    }
    .main-title { color: #ffffff; font-size: 3rem; line-height: 1.1; margin-bottom: 0px; margin-top: 20px;}
    .sub-title { color: #c69c6d; font-size: 1rem; letter-spacing: 3px; font-weight: 600; margin-bottom: 30px;}
    .section-header { color: #c69c6d; font-size: 1.5rem; margin-top: 30px; margin-bottom: 15px;}
    
    /* Input Fields */
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > div {
        background-color: #1e2127;
        color: #ffffff;
        border: 1px solid #333333;
    }
    .stTextInput > div > div > input:focus { border-color: #c69c6d; box-shadow: none; }
    
    /* Warning Box */
    .custom-warning {
        background-color: #3b4020;
        color: #d7ffd9;
        padding: 15px;
        border-radius: 5px;
        margin: 20px 0;
        font-size: 0.95rem;
    }
    
    /* Quote */
    .quote-text {
        color: #c69c6d;
        font-style: italic;
        margin-bottom: 20px;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #1e2127;
        color: #ffffff;
        border: 1px solid #c69c6d;
        border-radius: 4px;
        font-weight: 600;
        letter-spacing: 1px;
    }
    .stButton > button:hover {
        background-color: #c69c6d;
        color: #000000;
        border: 1px solid #c69c6d;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #16181c;
        border-right: 1px solid #333;
    }
    .sidebar-title { color: #c69c6d; font-size: 1.2rem; font-weight: bold; margin-bottom: 20px;}
    .sidebar-subtitle { color: #888888; font-size: 0.75rem; letter-spacing: 1px; margin-bottom: 10px;}
    
    /* Footer */
    .footer {
        text-align: center;
        margin-top: 50px;
        padding-top: 20px;
        border-top: 1px solid #333;
    }
    .footer h4 { color: #c69c6d; margin: 0; font-size: 1.2rem; letter-spacing: 2px;}
    .footer p { color: #666666; font-size: 0.8rem; letter-spacing: 1px; margin-top: 5px;}
</style>
""", unsafe_allow_html=True)

# Initialize database tables
db.init_db()

# ================= SESSION STATE =================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_data" not in st.session_state:
    st.session_state.user_data = {"name": "", "farm": "", "location": ""}
if "messages" not in st.session_state:
    st.session_state.messages = []

# ================= APPLICATION MIDDLEWARE =================
class AgriculturalMiddleware:
    """EA Application Layer: Dialect Normalization & Soft Guidance"""
    
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
You are the Seed 2 Harvest Strategic Agent.
SMME Partner: Shaun Cairns (Cape Town, South Africa).

INSTRUCTIONS:
1. Ground your advice in the certified product catalog:
{catalog_context}
2. Acknowledge user requests gracefully, providing the best possible agronomic or catalogue-backed answer.
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
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-title'>⛟ YOUR BASKET</div>", unsafe_allow_html=True)
    st.write("Empty")
    if st.button("CLEAR BASKET"):
        st.toast("Basket Cleared")
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("TERMINATE"):
        st.session_state.authenticated = False
        st.session_state.messages = []
        st.rerun()

# ================= MAIN HEADER =================
try:
    st.image("images/maxresdefault.jpg", use_container_width=True)
except Exception:
    st.markdown("<div style='height: 200px; background-color: #1a1e23; border: 1px solid #333;'></div>", unsafe_allow_html=True)

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
        
        st.markdown("""
        <div class="custom-warning">
            Hello fellow farmer. For the agent to work effectively we need permission to work with your data. Click yes to continue or leave.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='quote-text'>\"ubumfihlo ngundoqo\" — Ashley</div>", unsafe_allow_html=True)
        
        permission = st.checkbox("I GRANT PERMISSION")
        
        if st.button("AUTHORIZE ENTRY"):
            if client_name and client_farm and client_location and permission:
                st.session_state.user_data = {"name": client_name, "farm": client_farm, "location": client_location}
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Please complete all fields and grant permission to proceed.")

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

        normalized_prompt, detected_terms = AgriculturalMiddleware.normalize_vernacular(user_prompt)
        
        if not groq_client:
            st.error("SYSTEM ERROR: API connectivity offline.")
        else:
            try:
                chat_completion = groq_client.chat.completions.create(
                    model="llama3-8b-8192",  # Rock-solid, standard available Groq model
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Farmer Query: {normalized_prompt}"}
                    ],
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
    st.markdown("<div class='section-header'>CATALOGUE</div>", unsafe_allow_html=True)
    
    df_catalog = pd.DataFrame(
        catalog_data, 
        columns=["Product Name", "Category", "Available Stock", "Unit Price", "Application Guideline"]
    )
    df_catalog["Unit Price"] = df_catalog["Unit Price"].map("ZAR {:,.2f}".format)
    
    st.dataframe(df_catalog, use_container_width=True, hide_index=True)

elif page_selection == "📝 RESERVE ORDER":
    st.markdown("<div class='section-header'>RESERVE ORDER</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("FARM / COMPANY", value=st.session_state.user_data["farm"], disabled=True)
        st.text_input("LOCATION", value=st.session_state.user_data["location"], disabled=True)
        phone = st.text_input("CONTACT NUMBER")
    
    with col2:
        product_names = [p[0] for p in catalog_data]
        selected_product = st.selectbox("PRODUCT ALLOCATION", product_names)
        order_qty = st.number_input("VOLUME", min_value=1, max_value=500, value=1, step=1)
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("PROCESS TRANSACTION"):
        if not phone:
            st.error("Contact number required for transaction.")
        else:
            success, result = db.process_order_transaction(
                farmer_name=st.session_state.user_data["name"],
                phone=phone,
                location=st.session_state.user_data["location"],
                product_name=selected_product,
                quantity=order_qty
            )
            if success:
                st.success(f"Transaction Complete. Reference: ORD-{result['order_id']}")
                st.info(f"Allocated: {result['quantity']}x {result['product']} | Total: ZAR {result['total_cost']:,.2f}")
            else:
                st.error(f"Transaction Aborted: {result}")

elif page_selection == "⚙ GLOBAL FEED":
    st.markdown("<div class='section-header'>GLOBAL FEED & SYSTEM ARCHITECTURE</div>", unsafe_allow_html=True)
    st.markdown("""
    **ACTIVE SYSTEMS:**
    - **EA Middleware:** Python runtime translating regional vernacular & normalizing input streams.
    - **Persistence:** SQLite relational mapping (`orders`, `inventory`, `clients`).
    - **Compliance:** POPIA standards enforced on client data encapsulation.
    - **Inference Engine:** Groq LPU hardware routing to Llama-3 8B.
    """)

# ================= FOOTER =================
st.markdown("""
<div class='footer'>
    <h4>BUZUZI INCORPORATED</h4>
    <p>FOLLOW ON SOCIALS: @SEED2HARVEST_GLOBAL</p>
</div>
""", unsafe_allow_html=True)
