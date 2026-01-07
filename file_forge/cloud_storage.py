"""
Cloud Storage Connectors

Integrations for AWS S3, Google Drive, Azure Blob Storage, and Dropbox.
"""

import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, BinaryIO
from dataclasses import dataclass
import logging
import threading

logger = logging.getLogger(__name__)


@dataclass
class CloudFile:
    """Represents a file in cloud storage."""
    name: str
    path: str
    size: int
    modified_at: datetime
    content_type: Optional[str] = None
    metadata: Dict[str, str] = None


@dataclass
class CloudUploadResult:
    """Result of a cloud upload operation."""
    success: bool
    file_path: str
    url: Optional[str] = None
    error: Optional[str] = None


class CloudStorageProvider(ABC):
    """Abstract base class for cloud storage providers."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the storage provider."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the storage provider."""
        pass

    @abstractmethod
    def list_files(self, path: str = "") -> List[CloudFile]:
        """List files in a directory."""
        pass

    @abstractmethod
    def upload_file(
        self,
        local_path: str,
        remote_path: str,
        metadata: Dict[str, str] = None
    ) -> CloudUploadResult:
        """Upload a file to cloud storage."""
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download a file from cloud storage."""
        pass

    @abstractmethod
    def delete_file(self, remote_path: str) -> bool:
        """Delete a file from cloud storage."""
        pass


class S3StorageProvider(CloudStorageProvider):
    """AWS S3 storage provider."""

    def __init__(
        self,
        bucket_name: str,
        access_key: str = None,
        secret_key: str = None,
        region: str = "us-east-1",
        endpoint_url: str = None
    ):
        """Initialize S3 provider."""
        self.bucket_name = bucket_name
        self.access_key = access_key or os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = secret_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region = region
        self.endpoint_url = endpoint_url
        self.client = None
        self._connected = False

    def connect(self) -> bool:
        """Connect to S3."""
        try:
            import boto3
            self.client = boto3.client(
                's3',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                endpoint_url=self.endpoint_url
            )
            # Verify connection
            self.client.head_bucket(Bucket=self.bucket_name)
            self._connected = True
            logger.info(f"Connected to S3 bucket: {self.bucket_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to S3: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from S3."""
        self.client = None
        self._connected = False

    def list_files(self, path: str = "") -> List[CloudFile]:
        """List files in S3 bucket/path."""
        if not self._connected:
            self.connect()

        files = []
        prefix = path.lstrip('/')

        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )

            for obj in response.get('Contents', []):
                files.append(CloudFile(
                    name=obj['Key'].split('/')[-1],
                    path=obj['Key'],
                    size=obj['Size'],
                    modified_at=obj['LastModified']
                ))

        except Exception as e:
            logger.error(f"Failed to list S3 files: {e}")

        return files

    def upload_file(
        self,
        local_path: str,
        remote_path: str,
        metadata: Dict[str, str] = None
    ) -> CloudUploadResult:
        """Upload file to S3."""
        if not self._connected:
            self.connect()

        try:
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata

            self.client.upload_file(
                local_path,
                self.bucket_name,
                remote_path,
                ExtraArgs=extra_args
            )

            url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{remote_path}"

            return CloudUploadResult(
                success=True,
                file_path=remote_path,
                url=url
            )

        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            return CloudUploadResult(
                success=False,
                file_path=remote_path,
                error=str(e)
            )

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from S3."""
        if not self._connected:
            self.connect()

        try:
            self.client.download_file(
                self.bucket_name,
                remote_path,
                local_path
            )
            return True
        except Exception as e:
            logger.error(f"S3 download failed: {e}")
            return False

    def delete_file(self, remote_path: str) -> bool:
        """Delete file from S3."""
        if not self._connected:
            self.connect()

        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=remote_path
            )
            return True
        except Exception as e:
            logger.error(f"S3 delete failed: {e}")
            return False


class GoogleDriveProvider(CloudStorageProvider):
    """Google Drive storage provider."""

    def __init__(
        self,
        credentials_file: str = None,
        token_file: str = None
    ):
        """Initialize Google Drive provider."""
        self.credentials_file = credentials_file or os.getenv("GOOGLE_CREDENTIALS_FILE")
        self.token_file = token_file or os.getenv("GOOGLE_TOKEN_FILE")
        self.service = None
        self._connected = False

    def connect(self) -> bool:
        """Connect to Google Drive."""
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            creds = None
            if self.token_file and Path(self.token_file).exists():
                creds = Credentials.from_authorized_user_file(self.token_file)

            if not creds:
                logger.error("No Google Drive credentials found")
                return False

            self.service = build('drive', 'v3', credentials=creds)
            self._connected = True
            logger.info("Connected to Google Drive")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Google Drive: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from Google Drive."""
        self.service = None
        self._connected = False

    def list_files(self, path: str = "") -> List[CloudFile]:
        """List files in Google Drive."""
        if not self._connected:
            self.connect()

        files = []
        try:
            results = self.service.files().list(
                q=f"name contains '{path}'" if path else None,
                pageSize=100,
                fields="files(id, name, mimeType, size, modifiedTime)"
            ).execute()

            for item in results.get('files', []):
                files.append(CloudFile(
                    name=item['name'],
                    path=item['id'],
                    size=int(item.get('size', 0)),
                    modified_at=datetime.fromisoformat(
                        item['modifiedTime'].replace('Z', '+00:00')
                    ),
                    content_type=item.get('mimeType')
                ))

        except Exception as e:
            logger.error(f"Failed to list Google Drive files: {e}")

        return files

    def upload_file(
        self,
        local_path: str,
        remote_path: str,
        metadata: Dict[str, str] = None
    ) -> CloudUploadResult:
        """Upload file to Google Drive."""
        if not self._connected:
            self.connect()

        try:
            from googleapiclient.http import MediaFileUpload

            file_metadata = {
                'name': remote_path.split('/')[-1],
                'parents': [remote_path.rsplit('/', 1)[0]] if '/' in remote_path else []
            }

            media = MediaFileUpload(
                local_path,
                resumable=True
            )

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,webViewLink'
            ).execute()

            return CloudUploadResult(
                success=True,
                file_path=file['id'],
                url=file.get('webViewLink')
            )

        except Exception as e:
            logger.error(f"Google Drive upload failed: {e}")
            return CloudUploadResult(
                success=False,
                file_path=remote_path,
                error=str(e)
            )

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from Google Drive."""
        if not self._connected:
            self.connect()

        try:
            from googleapiclient.http import MediaIoBaseDownload

            request = self.service.files().get_media(fileId=remote_path)
            with open(local_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            return True

        except Exception as e:
            logger.error(f"Google Drive download failed: {e}")
            return False

    def delete_file(self, remote_path: str) -> bool:
        """Delete file from Google Drive."""
        if not self._connected:
            self.connect()

        try:
            self.service.files().delete(fileId=remote_path).execute()
            return True
        except Exception as e:
            logger.error(f"Google Drive delete failed: {e}")
            return False


class AzureBlobProvider(CloudStorageProvider):
    """Azure Blob Storage provider."""

    def __init__(
        self,
        account_name: str,
        account_key: str = None,
        container_name: str = "default"
    ):
        """Initialize Azure Blob provider."""
        self.account_name = account_name
        self.account_key = account_key or os.getenv("AZURE_ACCOUNT_KEY")
        self.container_name = container_name
        self.service = None
        self._connected = False

    def connect(self) -> bool:
        """Connect to Azure Blob Storage."""
        try:
            from azure.storage.blob import BlobServiceClient

            connection_string = (
                f"DefaultEndpointsProtocol=https;"
                f"AccountName={self.account_name};"
                f"AccountKey={self.account_key}"
            )

            self.service = BlobServiceClient.from_connection_string(
                connection_string
            )
            self._connected = True
            logger.info(f"Connected to Azure Blob Storage: {self.container_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Azure: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from Azure."""
        self.service = None
        self._connected = False

    def list_files(self, path: str = "") -> List[CloudFile]:
        """List files in Azure Blob container."""
        if not self._connected:
            self.connect()

        files = []
        try:
            container = self.service.get_container_client(self.container_name)
            prefix = path.strip('/')

            for blob in container.list_blobs(name_starts_with=prefix):
                files.append(CloudFile(
                    name=blob.name.split('/')[-1],
                    path=blob.name,
                    size=blob.size,
                    modified_at=blob.last_modified
                ))

        except Exception as e:
            logger.error(f"Failed to list Azure files: {e}")

        return files

    def upload_file(
        self,
        local_path: str,
        remote_path: str,
        metadata: Dict[str, str] = None
    ) -> CloudUploadResult:
        """Upload file to Azure Blob Storage."""
        if not self._connected:
            self.connect()

        try:
            from azure.storage.blob import ContentSettings

            container = self.service.get_container_client(self.container_name)
            blob = container.get_blob_client(remote_path)

            content_settings = None
            if metadata:
                content_settings = ContentSettings(
                    content_type=metadata.get('content_type', 'application/octet-stream')
                )

            with open(local_path, 'rb') as data:
                blob.upload_blob(
                    data,
                    overwrite=True,
                    content_settings=content_settings
                )

            return CloudUploadResult(
                success=True,
                file_path=remote_path,
                url=blob.url
            )

        except Exception as e:
            logger.error(f"Azure upload failed: {e}")
            return CloudUploadResult(
                success=False,
                file_path=remote_path,
                error=str(e)
            )

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from Azure."""
        if not self._connected:
            self.connect()

        try:
            container = self.service.get_container_client(self.container_name)
            blob = container.get_blob_client(remote_path)

            with open(local_path, 'wb') as f:
                blob.download_blob().readinto(f)
            return True

        except Exception as e:
            logger.error(f"Azure download failed: {e}")
            return False

    def delete_file(self, remote_path: str) -> bool:
        """Delete file from Azure."""
        if not self._connected:
            self.connect()

        try:
            container = self.service.get_container_client(self.container_name)
            blob = container.get_blob_client(remote_path)
            blob.delete_blob()
            return True

        except Exception as e:
            logger.error(f"Azure delete failed: {e}")
            return False


class CloudStorageManager:
    """Manager for multiple cloud storage providers."""

    def __init__(self):
        """Initialize cloud storage manager."""
        self.providers: Dict[str, CloudStorageProvider] = {}
        self._lock = threading.Lock()

    def register_provider(self, name: str, provider: CloudStorageProvider) -> None:
        """Register a cloud storage provider."""
        with self._lock:
            self.providers[name] = provider

    def get_provider(self, name: str) -> Optional[CloudStorageProvider]:
        """Get a registered provider."""
        return self.providers.get(name)

    def connect_all(self) -> Dict[str, bool]:
        """Connect to all registered providers."""
        results = {}
        for name, provider in self.providers.items():
            results[name] = provider.connect()
        return results

    def disconnect_all(self) -> None:
        """Disconnect from all providers."""
        for provider in self.providers.values():
            provider.disconnect()

    def sync_to_cloud(
        self,
        provider_name: str,
        local_dir: str,
        remote_dir: str = ""
    ) -> Dict[str, CloudUploadResult]:
        """Sync local directory to cloud storage."""
        provider = self.get_provider(provider_name)
        if not provider:
            raise ValueError(f"Provider {provider_name} not found")

        results = {}
        local_path = Path(local_dir)

        for file_path in local_path.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(local_path)
                remote_path = f"{remote_dir}/{rel_path}" if remote_dir else str(rel_path)
                results[str(file_path)] = provider.upload_file(
                    str(file_path),
                    remote_path
                )

        return results


# Initialize cloud storage manager
cloud_storage = CloudStorageManager()

# Register default providers
def init_cloud_providers():
    """Initialize cloud providers from environment."""
    # AWS S3
    if os.getenv("AWS_BUCKET_NAME"):
        cloud_storage.register_provider(
            "s3",
            S3StorageProvider(
                bucket_name=os.getenv("AWS_BUCKET_NAME"),
                access_key=os.getenv("AWS_ACCESS_KEY_ID"),
                secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region=os.getenv("AWS_REGION", "us-east-1")
            )
        )

    # Google Drive
    if os.getenv("GOOGLE_CREDENTIALS_FILE"):
        cloud_storage.register_provider(
            "google_drive",
            GoogleDriveProvider()
        )

    # Azure Blob
    if os.getenv("AZURE_ACCOUNT_NAME"):
        cloud_storage.register_provider(
            "azure",
            AzureBlobProvider(
                account_name=os.getenv("AZURE_ACCOUNT_NAME"),
                account_key=os.getenv("AZURE_ACCOUNT_KEY"),
                container_name=os.getenv("AZURE_CONTAINER", "default")
            )
        )
