from __future__ import annotations

from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient

from .models import Document


def create_adls_service_client(account_name: str) -> DataLakeServiceClient:
    """Create an ADLS Gen2 client using Microsoft Entra credentials."""
    if not account_name:
        raise ValueError("account_name is required")

    credential = DefaultAzureCredential()
    account_url = f"https://{account_name}.dfs.core.windows.net"
    return DataLakeServiceClient(account_url=account_url, credential=credential)


def list_paths(
    service_client: DataLakeServiceClient,
    file_system: str,
    directory: str | None = None,
) -> list[str]:
    """List paths under an ADLS Gen2 file system/directory."""
    file_system_client = service_client.get_file_system_client(file_system)
    return [
        item.name
        for item in file_system_client.get_paths(path=directory, recursive=True)
    ]


def load_text_file(
    service_client: DataLakeServiceClient,
    file_system: str,
    path: str,
    encoding: str = "utf-8",
) -> Document:
    """Download a text-like ADLS file and return it as a Document.

    Binary formats such as PDF/Excel should be downloaded first and handed to
    the appropriate parser/loader in the next learning stage.
    """
    file_system_client = service_client.get_file_system_client(file_system)
    file_client = file_system_client.get_file_client(path)
    data = file_client.download_file().readall()
    content = data.decode(encoding)

    return Document(
        content=content,
        metadata={
            "source_type": "adls_gen2",
            "source": path,
            "file_system": file_system,
            "path": path,
            "size_bytes": len(data),
        },
        id=f"adls://{file_system}/{path}",
    )
