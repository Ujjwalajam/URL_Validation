import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
from io import BytesIO
import base64
import os

st.set_page_config(page_title="URL Status Checker", layout="wide")
st.title("🔗 URL Status Checker (Excel Based with Resume)")

uploaded_file = st.file_uploader("📁 Upload Excel File (Must have a 'URL' column)", type=["xlsx"])
max_workers = st.slider("🔧 Select number of threads", 1, 20, 5)
checkpoint_interval = st.slider("💾 Checkpoint Save Interval", 1, 100, 25)
custom_filename = st.text_input("📄 Save output file as (without extension)", value="URL_Status_Result")

CHECKPOINT_DIR = "checkpoints"
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

def check_url(url):
    try:
        response = requests.get(url, timeout=5)
        return "Valid" if response.status_code == 200 else f"Error {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Invalid ({str(e)})"

def save_checkpoint(df, filename):
    df.to_excel(os.path.join(CHECKPOINT_DIR, f"checkpoint_{filename}.xlsx"), index=False)

def load_checkpoint(filename):
    path = os.path.join(CHECKPOINT_DIR, f"checkpoint_{filename}.xlsx")
    return pd.read_excel(path) if os.path.exists(path) else None

if uploaded_file:
    original_filename = uploaded_file.name.split(".")[0]
    checkpoint_data = load_checkpoint(original_filename)

    if checkpoint_data is not None:
        resume = st.radio("⚠️ Incomplete session found. Do you want to resume?", ["Yes", "No"])
        if resume == "Yes":
            df = checkpoint_data
        else:
            df = pd.read_excel(uploaded_file)
            df["Status"] = df.get("Status", pd.Series([None]*len(df)))
    else:
        df = pd.read_excel(uploaded_file)
        df["Status"] = df.get("Status", pd.Series([None]*len(df)))

    if "URL" not in df.columns:
        st.error("❌ Excel must contain a column named 'URL'")
    else:
        if st.button("🚀 Start Checking"):
            progress_bar = st.progress(0)
            status_placeholder = st.empty()
            total = len(df)
            
            def get_unchecked_indices():
                return df[df['Status'].isnull()].index.tolist()

            indices_to_check = get_unchecked_indices()

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for i, idx in enumerate(indices_to_check):
                    url = df.at[idx, "URL"]
                    future = executor.submit(check_url, url)
                    df.at[idx, "Status"] = future.result()

                    if (i + 1) % checkpoint_interval == 0 or i == len(indices_to_check) - 1:
                        save_checkpoint(df, original_filename)

                    progress = int(((i + 1) / len(indices_to_check)) * 100)
                    progress_bar.progress(progress)
                    status_placeholder.info(f"Processed {i + 1} / {len(indices_to_check)} URLs")

            st.success("✅ URL Checking Completed!")
            st.dataframe(df)

            # Save final output
            output = BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)

            b64 = base64.b64encode(output.read()).decode()
            download_filename = f"{custom_filename}.xlsx"
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="{download_filename}">📥 Download {download_filename}</a>'
            st.markdown(href, unsafe_allow_html=True)

            # Remove checkpoint
            os.remove(os.path.join(CHECKPOINT_DIR, f"checkpoint_{original_filename}.xlsx"))
            st.info("🗑️ Temporary checkpoint file removed after success.")
