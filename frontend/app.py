"""Optional Streamlit entry. Prefer: streamlit run app.py from the project root."""

import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parent.parent / "app.py"), run_name="__main__")
