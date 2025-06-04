import pandas as pd
import requests
import streamlit as st
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import base64
import os
import time

st.set_page_config(page_title="URL Status Checker", layout="wide")
st.title("🔗 URL Status Checker with Resume and Progress")

CHECKPOINT_FILE = "checkpoint_result.csv"
DEFAULT_THREADS = 20

# ---- Functions ----
def check_url(url):
    try:
        response = requests.get(url, timeout=5)
        return "Valid" if response.status_code == 200 else f"Error {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Invalid ({str(e)})"

def process_urls_with_progress(df, status_column="Status"):
    total = len(df)
    completed = 0
    batch_size = 10
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=DEFAULT_THREADS) as executor:
        futures = {}
        for idx, row in df.iterrows():
            if pd.notna(row[status_column]):
                completed += 1
                continue
            futures[executor.submit(check_url, row['URL'])] = idx
            if len(futures) >= batch_size:
                for future in futures:
                    df.at[futures[future], status_column] = future.result()
                    completed += 1

                futures.clear()

                elapsed = time.time() - start_time
                avg_time = elapsed / completed if completed else 1
                remaining_time = int((total - completed) * avg_time)

                st.progress(completed / total)
                st.info(f"✅ Checked: {completed}/{total} | ⏳ Est. time left: {remaining_time}s")

                # Save checkpoint
                df.to_csv(CHECKPOINT_FILE, index=False)

        # Final remaining futures
        for future in futures:
            df.at[futures[future], status_column] = future.result()
            completed += 1

        st.progress(1.0)
        st.success("🎉 URL Checking Completed!")
        df.to_csv(CHECKPOINT_FILE, index=False)
        return df

# ---- Sample File Option ----
with st.expander("📄 Download Sample File"):
    sample_df = pd.DataFrame({"URL": ["https://www.google.com", "https://invalid.url.test"]})
    sample_io = BytesIO()
    sample_df.to_excel(sample_io, index=False)
    sample_io.seek(0)
    sample_b64 = base64.b64encode(sample_io.read()).decode()
    sample_link = f'<a href="data:application/octet-stream;base64,{sample_b64}" download="sample_URLs.xlsx">📥 Download Sample Excel</a>'
    st.markdown(sample_link, unsafe_allow_html=True)

# ---- File Upload & Main Logic ----
uploaded_file = st.file_uploader("📁 Upload Excel File (must contain 'URL' column)", type=["xlsx"])
custom_name = st.text_input("💾 Output File Name (without extension)", value="URL_Check_Results")

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    if 'URL' not in df.columns:
        st.error("❌ Uploaded file must contain a column named 'URL'")
    else:
        # Initialize status column
        if 'Status' not in df.columns:
            df['Status'] = None

        # Load checkpoint if exists
        if os.path.exists(CHECKPOINT_FILE):
            try:
                checkpoint_df = pd.read_csv(CHECKPOINT_FILE)
                if checkpoint_df.shape[0] == df.shape[0]:
                    df = checkpoint_df
                    st.info("🔁 Resumed from last checkpoint.")
            except Exception as e:
                st.warning("⚠️ Could not load checkpoint. Starting fresh.")

        if st.button("🚀 Start URL Checking"):
            with st.spinner("Working..."):
                df = process_urls_with_progress(df)

            # Output to Excel
            output = BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)
            b64 = base64.b64encode(output.read()).decode()
            filename = f"{custom_name}.xlsx"
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">📥 Download Final File</a>'
            st.markdown(href, unsafe_allow_html=True)

            # Remove checkpoint file after successful run
            os.remove(CHECKPOINT_FILE)
