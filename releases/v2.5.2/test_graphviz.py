import streamlit as st
import graphviz

try:
    dot = graphviz.Digraph()
    dot.node('A', 'Start')
    dot.node('B', 'End')
    dot.edge('A', 'B')
    print("Graphviz import successful")
except Exception as e:
    print(f"Graphviz error: {e}")
