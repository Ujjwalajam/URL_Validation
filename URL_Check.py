import pandas as pd
import requests
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
import base64
import os
import time

st.set_page_config(page_title="URL Status Checker", layout="wide")
st.title("🔗 Fast URL Status Checker with Resume")

CHECKPOINT_FILE = "checkpoint_result.csv"
THREADS = 20

def check_url(url):
    try:
        response = requests.get(url, timeout=5)
        return "Valid" if response.status_code == 200 else f"Error {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Invalid ({str(e)})"

def process_urls(df):
    total = len(df)
    pending_rows = df[df['Status'].isna()].copy()

    completed = total - len(pending_rows)
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(check_url, row['URL']): idx for idx, row in pending_rows.iterrows()}

        for i, future in enumerate(as_completed(futures), start=1):
            idx = futures[future]
            df.at[idx, 'Status'] = future.result()

            # Show single-line live progress
            elapsed = time.time() - start_time
            done = completed + i
            remaining = (elapsed / done) * (total - done) if done else 0
            st.info(f"✔️ Checked: {done}/{total} | ⏳ Time left: {remaining/60:.1f} min")

    df.to_csv(CHECKPOINT_FILE, index=False)
    return df

uploaded_file = st.file_uploader("📁 Upload Excel File (must have 'URL' column)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    if 'URL' not in df.columns:
        st.error("❌ 'URL' column not found in uploaded file.")
    else:
        if 'Status' not in df.columns:
            df['Status'] = None

        # Resume logic
        if os.path.exists(CHECKPOINT_FILE):
            try:
                checkpoint_df = pd.read_csv(CHECKPOINT_FILE)
                if checkpoint_df.shape[0] == df.shape[0]:
                    df = checkpoint_df
                    st.info("🔁 Resuming from last checkpoint.")
            except Exception:
                st.warning("⚠️ Couldn't load checkpoint. Starting fresh.")

        if st.button("🚀 Start Checking"):
            with st.spinner("Checking URLs..."):
                df = process_urls(df)

            output = BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)

            b64 = base64.b64encode(output.read()).decode()
            download_link = f'<a href="data:application/octet-stream;base64,{b64}" download="URL_Status_Result.xlsx">📥 Download Result</a>'
            st.markdown(download_link, unsafe_allow_html=True)

            if os.path.exists(CHECKPOINT_FILE):
                os.remove(CHECKPOINT_FILE)
            st.success("✅ Completed and checkpoint cleared.")
