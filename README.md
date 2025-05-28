# 🔗 URL Status Checker

This is a simple web-based Streamlit app that checks the status of URLs from an uploaded Excel file.

## ✅ Features
- Upload an Excel file with a `URL` column
- Checks each URL and returns its status (Valid / Invalid)
- Multi-threaded checking (customizable thread count)
- Download the results as an Excel file

## 🚀 How to Use
1. Visit the deployed Streamlit app (after deploying).
2. Upload your Excel file.
3. Start the URL check.
4. Download the final result.

## 📦 Requirements
- streamlit
- pandas
- requests
- openpyxl

## 📤 Deployment
1. Push this code to GitHub
2. Deploy it on [Streamlit Cloud](https://streamlit.io/cloud)

## 📁 Sample Excel Format

| URL                        |
|----------------------------|
| https://www.google.com     |
| https://www.invalidsite.xyz |
