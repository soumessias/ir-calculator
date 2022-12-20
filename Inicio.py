import streamlit as st
import pandas as pd
import os
os.system('clear')

# Run Streamlit Command: streamlit run Inicio.py --theme.base "light"

st.title("IR Calculator by Messias")

markdown_label = '''
The following list won't indent no matter what I try:
- Item 1
- Item 2
- Item 3
'''
with st.sidebar:
    st.title("Upload your CSV")
    uploaded_file = st.file_uploader(
        markdown_label,
        type='csv',
        key='transaction_dataset'
    )
if uploaded_file is not None:
    transaction_df = pd.read_csv(uploaded_file)
    st.write(transaction_df)