import subprocess
import sys

subprocess.run([sys.executable, "-m", "streamlit", "run", "frontend/streamlit_app.py"], check=True)
