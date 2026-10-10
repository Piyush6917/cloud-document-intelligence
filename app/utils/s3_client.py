from pathlib import Path


class S3Client:
    def __init__(self, bucket: str | None, region: str | None = None, prefix: str = "documents") -> None:
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.region = region
        self._client = None

    @property
    def client(self):
        if not self.bucket:
            raise RuntimeError("S3_BUCKET is not configured")
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client("s3", region_name=self.region)
            except ImportError as exc:
                raise RuntimeError("boto3 is required for S3 integration") from exc
        return self._client

    def upload(self, path: Path, key: str | None = None) -> str:
        object_key = f"{self.prefix}/{key or path.name}"
        self.client.upload_file(str(path), self.bucket, object_key,
                                ExtraArgs={"ContentType": "application/pdf"})
        return object_key

    def download(self, key: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.client.download_file(self.bucket, key, str(destination))