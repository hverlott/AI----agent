import streamlit as st

try:
    st.graphviz_chart('digraph { A -> B }')
    print("st.graphviz_chart works")
except Exception as e:
    print(f"st.graphviz_chart error: {e}")
