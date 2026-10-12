import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import os
from groq import Groq

# 1. INITIALIZE FIREBASE SECURELY
if not firebase_admin._apps:
    firebase_credentials = dict(st.secrets["firebase"])
    cred = credentials.Certificate(firebase_credentials)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# 2. INITIALIZE GROQ CLIENT
# Ensure you add your Groq API key to your .streamlit/secrets.toml as well!
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.set_page_config(page_title="Seed2Harvest Agent", page_icon="🌱")
st.title("Seed2Harvest Agri-Agent")

# 3. FIREBASE HELPER FUNCTIONS
def get_inventory_context():
    """Fetches the latest catalog/inventory from Firestore to feed to the AI."""
    docs = db.collection("inventory").stream()
    inventory_data = ""
    for doc in docs:
        item = doc.to_dict()
        inventory_data += f"- {item.get('product_name')}: R{item.get('price')} (Stock: {item.get('stock_level')})\n"
    return inventory_data

def save_chat_to_db(role, content):
    """Logs the chat history to Firebase for the audit trail/monitoring."""
    db.collection("chat_logs").document().set({
        "role": role,
        "content": content,
        "timestamp": firestore.SERVER_TIMESTAMP
    })

# 4. CHAT INTERFACE & STATE MANAGEMENT
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. AGENT LOGIC
if prompt := st.chat_input("Ask about seeds, harvesting, or pricing..."):
    # Display user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_chat_to_db("user", prompt)

    # Fetch live database context
    live_inventory = get_inventory_context()

    # System prompt enforcing your specific design boundaries
    system_prompt = f"""
    You are the official conversational AI for the agricultural small business Seed2Harvest. 
    You must comprehend agricultural slang and misspellings common among local farmers, but you MUST strictly reply in professional, standard language. Do not use slang in your responses.
    
    Base your answers ONLY on the following real-time inventory data from our database:
    {live_inventory}
    
    If a user asks about a product not in this list, politely inform them it is out of stock or unavailable.
    """

    # Build message array for the Groq API
    api_messages = [{"role": "system", "content": system_prompt}]
    for msg in st.session_state.messages:
        api_messages.append({"role": msg["role"], "content": msg["content"]})

    # Call Groq API
    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192", # Or your preferred model
            messages=api_messages,
            temperature=0.3,
        )
        response = completion.choices[0].message.content
        
        # Display assistant response
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        save_chat_to_db("assistant", response)
        
    except Exception as e:
        st.error(f"Error communicating with the intelligence layer: {e}")
