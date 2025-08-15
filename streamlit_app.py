# streamlit_app.py
import streamlit as st
from bots_checker import validate_url, crawl_with_user_agents

st.set_page_config(page_title="AI Bots Checker", layout="wide")
st.title("🤖 AI Bots Accessibility Checker")

url = st.text_input("Enter website URL (with http/https):", "")

if st.button("Run Check"):
    if not validate_url(url):
        st.error("Invalid URL. Please enter a valid one starting with http:// or https://")
    else:
        with st.spinner("Checking bots access..."):
            results = crawl_with_user_agents(url)
        st.success("Done!")
        st.dataframe(results)
