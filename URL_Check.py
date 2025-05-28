import streamlit as st
import pandas as pd
import requests
import io
import time

st.set_page_config(page_title="URL Validator", layout="centered")
st.title("🔗 URL Validation Tool")
st.write("Upload an Excel file with a column named **URL** to validate links.")

# ---------------- Sample File Download ---------------- #
sample_df = pd.DataFrame({'URL': ['https://example.com', 'https://openai.com']})
sample_excel = io.BytesIO()
sample_df.to_excel(sample_excel, index=False)
sample_excel.seek(0)

st.download_button(
    label="📄 Download Sample Excel File",
    data=sample_excel,
    file_name="Sample_URL_File.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# ---------------- Upload Section ---------------- #
uploaded_file = st.file_uploader("📤 Upload your Excel file", type=["xlsx"])

def check_url(url):
    try:
        response = requests.get(url, timeout=5)
        return "Valid" if response.status_code == 200 else f"Error {response.status_code}"
    except requests.exceptions.RequestException:
        return "Invalid"

# ---------------- Process Logic ---------------- #
if uploaded_file:
    df = pd.read_excel(uploaded_file)

    if 'URL' not in df.columns:
        st.error("❌ The uploaded file must contain a column named 'URL'.")
    else:
        urls = df['URL'].tolist()
        st.info(f"🔎 Found {len(urls)} URLs. Starting validation...")

        progress_bar = st.progress(0)
        status_area = st.empty()
        results = []

        start_time = time.time()
        for i, url in enumerate(urls):
            status_area.text(f"Processing {i+1} of {len(urls)}: {url}")
            result = check_url(url)
            results.append(result)
            progress = (i + 1) / len(urls)
            progress_bar.progress(progress)

        end_time = time.time()
        elapsed = end_time - start_time

        df['Status'] = results
        st.success(f"✅ Validation complete in {round(elapsed, 2)} seconds!")

        # Download final result
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)

        st.download_button(
            label="⬇️ Download Results Excel",
            data=output,
            file_name="URL_Validation_Results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
