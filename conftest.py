# conftest.py  (place at project root, next to streamlit_app.py)
import sys
import os

# Adds the project root to sys.path so pytest can find
# utils/, services/, and pac_server_repo/ as top-level modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))