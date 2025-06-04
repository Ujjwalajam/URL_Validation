import pandas as pd
import requests
import streamlit as st
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import base64
import os
import pickle

st.set_page_config(page_title="URL Status Checker", layout="wide")
st.title("🔗 URL Status Checker with Resume Support")

CHECKPOINT_FILE = "checkpoint.pkl"
DEFAULT_THREADS = 20
SAVE_INTERVAL = 20  # Save progress every 20 rows

uploaded_file = st.file_uploader("📁 Upload Excel File (Must have a 'URL' column)", type=["xlsx"])
resume_enabled = st.checkbox("🔄 Enable Resume Progress if Interrupted", value=True)
save_filename = st.text_input("💾 Enter name to save result file as", value="URL_Status_Result")


def check_url(url):
    try:
        response = requests.get(url, timeout=5)
        return "Valid" if response.status_code == 200 else f"Error {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Invalid ({str(e)})"


def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'rb') as f:
            return pickle.load(f)
    return None


def save_checkpoint(index, status_list):
    with open(CHECKPOINT_FILE, 'wb') as f:
        pickle.dump((index, status_list), f)


def delete_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    if 'URL' not in df.columns:
        st.error("❌ Excel must contain a column named 'URL'")
    else:
        if st.button("🚀 Start Checking"):
            if resume_enabled:
                checkpoint = load_checkpoint()
            else:
                checkpoint = None

            if checkpoint:
                start_index, results = checkpoint
                st.warning(f"⚠️ Resuming from row {start_index}...")
            else:
                start_index, results = 0, []

            with st.spinner("Checking URLs... This may take a while."):
                urls_to_check = df['URL'].tolist()
                total = len(urls_to_check)
                progress_bar = st.progress(0)

                with ThreadPoolExecutor(max_workers=DEFAULT_THREADS) as executor:
                    for i in range(start_index, total, DEFAULT_THREADS):
                        end = min(i + DEFAULT_THREADS, total)
                        chunk = urls_to_check[i:end]
                        chunk_results = list(executor.map(check_url, chunk))
                        results.extend(chunk_results)

                        current_index = end
                        if resume_enabled and (current_index % SAVE_INTERVAL == 0 or current_index == total):
                            save_checkpoint(current_index, results)

                        progress_bar.progress(min(current_index / total, 1.0))

                df = df.iloc[:len(results)]
                df['Status'] = results
                delete_checkpoint()

                st.success("✅ URL Checking Completed!")
                st.dataframe(df)

                output = BytesIO()
                df.to_excel(output, index=False)
                output.seek(0)

                b64 = base64.b64encode(output.read()).decode()
                href = f'<a href="data:application/octet-stream;base64,{b64}" download="{save_filename}.xlsx">📥 Download Result</a>'
                st.markdown(href, unsafe_allow_html=True)

        with st.expander("📄 Need a sample file?"):
            sample_df = pd.DataFrame({"URL": ["https://www.google.com", "https://www.invalidurl1234.com"]})
            sample_output = BytesIO()
            sample_df.to_excel(sample_output, index=False)
            sample_output.seek(0)
            b64_sample = base64.b64encode(sample_output.read()).decode()
            href_sample = f'<a href="data:application/octet-stream;base64,{b64_sample}" download="Sample_URL_File.xlsx">📥 Download Sample File</a>'
            st.markdown(href_sample, unsafe_allow_html=True)
