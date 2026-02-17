import streamlit as st
import utils

utils.check_auth()
utils.render_header()

st.title("Admin Dashboard 🛠️")

if st.session_state.get('role') != 'admin':
    st.error("Access Denied. This page is for Admins only.")
    st.stop()
    
st.header("System Health")
st.success("All Systems Operational")
st.write("Database: Connected")
st.write("AI Agents: Online")

utils.render_footer()
