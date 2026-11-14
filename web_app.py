
import streamlit as st

st.set_page_config(
    page_title="SpendMate AI",
    page_icon="💰",
    layout="wide"
)

st.title("💰 SpendMate AI")
st.subheader("Smart Personal Finance Management")

st.success("Welcome to SpendMate AI Web Application!")

st.write("Track your income, expenses and savings in one place.")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Income", "₹0")

with col2:
    st.metric("Total Expenses", "₹0")

with col3:
    st.metric("Total Savings", "₹0")

st.info("Your online finance dashboard is ready for development.")
