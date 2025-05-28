import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
from io import BytesIO
import base64
import io
import time

# Sample DataFrame for download
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

st.set_page_config(page_title="URL Status Checker", layout="wide")
st.title("🔗 URL Status Checker (Excel Based)")

uploaded_file = st.file_uploader("📁 Upload Excel File (Must have a 'URL' column)", type=["xlsx"])
max_workers = st.slider("🔧 Select number of threads", 1, 20, 5)

def check_url(url):
    try:
        response = requests.get(url, timeout=5)
        return "Valid" if response.status_code == 200 else f"Error {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Invalid ({str(e)})"

def process_urls(urls):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(check_url, urls))
    return results

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    if 'URL' not in df.columns:
        st.error("❌ Excel must contain a column named 'URL'")
    else:
        if st.button("🚀 Start Checking"):
            with st.spinner("Checking URLs..."):
                df['Status'] = process_urls(df['URL'])
                st.success("✅ URL Checking Completed!")

                st.dataframe(df)

                output = BytesIO()
                df.to_excel(output, index=False)
                output.seek(0)

                b64 = base64.b64encode(output.read()).decode()
                href = f'<a href="data:application/octet-stream;base64,{b64}" download="URL_Status_Result.xlsx">📥 Download Result</a>'
                st.markdown(href, unsafe_allow_html=True)
st.subheader("🛠️ URL Checking")

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    urls = df['URL'].tolist()

    progress_bar = st.progress(0)
    status_text = st.empty()
    results = []

    for i, url in enumerate(urls):
        status_text.text(f"Checking URL {i+1} of {len(urls)}")
        result = check_url(url)
        results.append(result)
        progress_bar.progress((i + 1) / len(urls))
        # Optional: delay to simulate processing
        # time.sleep(0.1)

    df['Status'] = results
    st.success("✅ URL validation complete!")
