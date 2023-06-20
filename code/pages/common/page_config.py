import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def load_page_config():
    st.set_page_config(
        layout="wide",
        page_title=os.getenv("PAGE_TITLE"),
        page_icon=os.path.join('images', 'openai.ico'),
        menu_items={
            'Get help': None,
            'Report a bug': None,
            'About': None
        }
    )

    hide_streamlit_style = """
                    <style>
                    #MainMenu {visibility: hidden;}
                    footer {visibility: hidden;}
                    </style>
                    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
