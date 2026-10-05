import sys
import os
import platform
import importlib
import streamlit as st

st.set_page_config(page_title="Seed 2 Harvest Diagnostics")
st.title("Seed 2 Harvest: startup diagnostics")
st.caption("If you can read this page, Streamlit Cloud itself is working. Each line below shows what passes or fails.")

st.subheader("Environment")
st.write(f"Python: {sys.version.split()[0]} ({platform.platform()})")
st.write(f"Streamlit: {st.__version__}")
st.write(f"Working directory: {os.getcwd()}")
st.write("Files here: " + ", ".join(sorted(os.listdir("."))[:40]))

st.subheader("Packages")
for mod in ["streamlit", "pandas", "qrcode", "PIL", "requests", "groq"]:
    try:
        m = importlib.import_module(mod)
        st.success(f"{mod} OK {getattr(m, '__version__', '')}")
    except Exception as e:
        st.error(f"{mod} FAILED: {e}")

st.subheader("Database")
try:
    import The_Database as db
    db.init_db()
    rows = db.fetch_inventory()
    st.success(f"Database OK, {len(rows)} products found")
except Exception as e:
    st.error(f"Database FAILED: {e}")

st.subheader("Banner image")
path = "images/maxresdefault.jpg"
if os.path.exists(path):
    st.success(f"{path} found, {os.path.getsize(path) // 1024} KB")
else:
    st.warning(f"{path} not found (the app falls back to a plain bar)")

st.subheader("Secrets")
try:
    names = list(st.secrets.keys())
    st.write("Secret names present: " + (", ".join(names) if names else "none"))
    st.write("GROQ_API_KEY present: " + str("GROQ_API_KEY" in names))
except Exception as e:
    st.warning(f"No secrets file found: {e}")

st.subheader("Groq client")
try:
    from groq import Groq
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        try:
            key = st.secrets["GROQ_API_KEY"]
        except Exception:
            key = None
    if key:
        Groq(api_key=key)
        st.success("Groq client created OK")
    else:
        st.warning("No GROQ_API_KEY set, chat will show 'API connectivity offline'")
except Exception as e:
    st.error(f"Groq client FAILED: {e}")

st.subheader("Main app syntax check")
try:
    with open("app.py", encoding="utf-8") as f:
        compile(f.read(), "app.py", "exec")
    st.success("app.py compiles OK")
except Exception as e:
    st.error(f"app.py FAILED to compile: {e}")
