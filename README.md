# Cloud Document Intelligence

Local-first PDF retrieval application with a FastAPI backend, FAISS semantic search, Sentence Transformers embeddings, and an optional Streamlit UI. Document text is treated as untrusted data; the application does not execute PDF content or claim to generate an answer when no evidence is found.

## Prerequisites

- Python 3.11
- PowerShell on Windows
- Optional: Docker Desktop

## Windows PowerShell setup

Run these commands from the project root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

The embedding model is downloaded by Sentence Transformers the first time indexing runs. This requires internet access, but no AWS credentials.

## Run locally

Terminal 1:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

Terminal 2:

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run frontend.py
```

Open `http://localhost:8501`. The API is available at `http://localhost:8000/docs`.

## Workflow

1. Upload PDFs through the UI or `POST /documents/upload`.
2. Select **Index documents**. Text is extracted page by page, chunked, embedded, and stored in `models/`.
3. Ask a question. Results include source PDF names, pages, excerpts, and similarity scores.
4. After adding or deleting files, index again to rebuild the complete index.

Example API commands:

```powershell
curl.exe http://localhost:8000/health
curl.exe -F "file=@data\example.pdf" http://localhost:8000/documents/upload
curl.exe -X POST http://localhost:8000/documents/index
curl.exe -H "Content-Type: application/json" -d "{\"question\":\"What is this document about?\"}" http://localhost:8000/chat
```

## Tests

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest
```

Tests use synthetic PDFs and do not use private documents, AWS, or a generative model.

## Docker

```powershell
docker compose up --build
```

The API is on port 8000 and Streamlit is on port 8501. `data/` and `models/` are mounted so PDFs and indexes persist locally. Do not copy `.env` or private PDFs into an image.

## AWS option

S3 support is intentionally optional. Set `S3_BUCKET` and `AWS_REGION` in an environment (never in source control), use an EC2 instance profile or another standard AWS credential provider, and grant only the required `s3:GetObject` and `s3:PutObject` permissions for the configured prefix. Use private buckets with encryption and block public access. CloudWatch can collect application logs, and ECR can store a built image. GitHub Actions should run tests and build the image, but deployment must be explicitly configured; this project never creates live AWS resources automatically.

For cost control, stop or terminate unused EC2 instances, remove old ECR images, set S3 lifecycle expiration for temporary objects, and delete unused indexes and test buckets.

## Troubleshooting

- `sentence-transformers is required`: activate the virtual environment and install `requirements.txt`.
- Model download errors: verify internet access, or pre-cache the configured model in the runtime image.
- `No extractable text`: the PDF is likely scanned and requires a separately configured OCR pipeline.
- FAISS dimension errors: delete `models/index.faiss` and `models/metadata.json`, then index again.
- `413`: increase `MAX_UPLOAD_SIZE_MB` only when appropriate.