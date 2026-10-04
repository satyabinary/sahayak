from __future__ import annotations

import os
from pathlib import Path
import tempfile

import streamlit as st


def save_uploaded_image(uploaded_file) -> str:
    if uploaded_file is None:
        raise ValueError("No file provided.")

    output_dir = Path("./data/uploads")
    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(uploaded_file.name).suffix or ".png"
    file_path = output_dir / f"temp_upload_{abs(hash(uploaded_file.name))}{suffix}"
    with file_path.open("wb") as handle:
        handle.write(uploaded_file.getvalue())
    return str(file_path)
