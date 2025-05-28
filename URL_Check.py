import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
from io import BytesIO
import base64
import time

st.set_page_config(page_title="URL Status Checker", layout="wide")
st.title("🔗 URL Status Checker (Excel Based)")

# 1. Sample file download
st.subheader("📄 Sample Excel File")
sample_df = pd.DataFrame({'URL': ['https://www.google.com', 'https://www.example.com']})
sample_buffer = BytesIO()
sample_df.to_excel(sample_buffer, index=False)
sample_buffer.seek(0)
st.download_button(
    label="📥 Download Sample Excel",
    data=sample_buffer,
    file_name="Sample_URL_List.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# 2. File uploader
st.subheader("📁 Upload Your Excel File")
uploaded_file = st.file_uploader("Upload Excel file with a column named 'URL'", type=["xlsx"])

# 3. Slider for thread control
max_workers = st.slider("🔧 Select number of threads", 1, 20, 5)

# 4. URL checking function
def check_url(url):
    try:
        response = requests.get(url, timeout=5)
        return "Valid" if response.status_code == 200 else f"Error {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Invalid ({str(e)})"

# 5. Threaded processing with progress
def process_urls_with_progress(urls):
    results = []
    total = len(urls)
    start = time.time()
    progress_bar = st.progress(0)
    status_text = st.empty()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i, result in enumerate(executor.map(check_url, urls)):
            results.append(result)
            elapsed = time.time() - start
            estimated_total = (elapsed / (i + 1)) * total
            remaining = estimated_total - elapsed
            progress_bar.progress((i + 1) / total)
            status_text.text(
                f"⏳ Processing {i+1}/{total} | "
                f"Elapsed: {round(elapsed, 1)}s | "
                f"ETA: {round(remaining, 1)}s"
            )

    return results

# 6. Main logic
if uploaded_file:
    df = pd.read_excel(uploaded_file)

    if 'URL' not in df.columns:
        st.error("❌ Excel must contain a column named 'URL'")
    else:
        if st.button("🚀 Start URL Checking"):
            with st.spinner("Checking URLs..."):
                df['Status'] = process_urls_with_progress(df['URL'])
                st.success("✅ URL Checking Completed!")
                # st.dataframe(df)

                # Convert to downloadable file
                output = BytesIO()
                df.to_excel(output, index=False)
                output.seek(0)
                b64 = base64.b64encode(output.read()).decode()
                href = f'<a href="data:application/octet-stream;base64,{b64}" download="URL_Status_Result.xlsx">📥 Download Result</a>'
                st.markdown(href, unsafe_allow_html=True)
