import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
from io import BytesIO
import base64

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
