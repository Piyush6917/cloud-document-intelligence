import os

import requests
import streamlit as st

API = st.sidebar.text_input("API URL", os.getenv("BACKEND_URL", "http://localhost:8000"))
st.title("Cloud Document Intelligence")

uploads = st.file_uploader("Upload PDF documents", type=["pdf"], accept_multiple_files=True)
if st.button("Upload") and uploads:
    for uploaded in uploads:
        response = requests.post(f"{API}/documents/upload",
                                 files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")})
        st.write(response.json())
if st.button("Index documents"):
    response = requests.post(f"{API}/documents/index")
    st.write(response.json())

st.subheader("Documents")
try:
    documents = requests.get(f"{API}/documents", timeout=5).json()
    for document in documents:
        st.write(f"{document['name']} ({document['size']} bytes)")
except requests.RequestException as exc:
    st.error(f"API unavailable: {exc}")

question = st.text_input("Ask a question")
if st.button("Ask") and question:
    response = requests.post(f"{API}/chat", json={"question": question})
    if response.ok:
        result = response.json()
        st.write(result["answer"])
        for source in result["sources"]:
            st.caption(f"{source['source']} p.{source['page']} (score {source['score']:.3f})")
    else:
        st.error(response.text)
