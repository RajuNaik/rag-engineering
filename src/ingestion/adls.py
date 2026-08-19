from __future__ import annotations

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient


def create_adls_service_client(account_name: str) -> DataLakeServiceClient:
    """Create an ADLS Gen2 client using Microsoft Entra credentials."""
    if not account_name:
        raise ValueError("account_name is required")

    credential = DefaultAzureCredential()
    account_url = f"https://{account_name}.dfs.core.windows.net"
    return DataLakeServiceClient(account_url=account_url, credential=credential)


def _ensure_directory(service_client: DataLakeServiceClient, file_system: str, directory: str) -> None:
    """Create an ADLS directory tree if it does not already exist."""
    if not directory:
        return

    directory_client = service_client.get_file_system_client(file_system).get_directory_client(directory)
    try:
        directory_client.create_directory()
    except ResourceExistsError:
        pass


def upload_bytes(
    service_client: DataLakeServiceClient,
    file_system: str,
    path: str,
    data: bytes,
) -> None:
    """Upload bytes to ADLS Gen2, creating parent directories as needed."""
    parent = "/".join(path.split("/")[:-1])
    _ensure_directory(service_client, file_system, parent)

    file_client = service_client.get_file_system_client(file_system).get_file_client(path)
    file_client.upload_data(data, overwrite=True)


def upload_text(
    service_client: DataLakeServiceClient,
    file_system: str,
    path: str,
    content: str,
    encoding: str = "utf-8",
) -> None:
    """Upload text content to ADLS Gen2."""
    upload_bytes(service_client, file_system, path, content.encode(encoding))


def path_exists(
    service_client: DataLakeServiceClient,
    file_system: str,
    path: str,
) -> bool:
    """Return True when an ADLS file exists."""
    file_system_client = service_client.get_file_system_client(file_system)
    try:
        file_system_client.get_file_client(path).get_file_properties()
        return True
    except ResourceNotFoundError:
        return False


def read_text(
    service_client: DataLakeServiceClient,
    file_system: str,
    path: str,
    encoding: str = "utf-8",
) -> str:
    """Download a text file from ADLS Gen2."""
    file_system_client = service_client.get_file_system_client(file_system)
    file_client = file_system_client.get_file_client(path)
    data = file_client.download_file().readall()
    return data.decode(encoding)


def list_paths(
    service_client: DataLakeServiceClient,
    file_system: str,
    directory: str | None = None,
) -> list[str]:
    """List paths under an ADLS Gen2 file system/directory."""
    file_system_client = service_client.get_file_system_client(file_system)
    return [item.name for item in file_system_client.get_paths(path=directory, recursive=True)]


def load_text_file(
    service_client: DataLakeServiceClient,
    file_system: str,
    path: str,
    encoding: str = "utf-8",
):
    """Backward-compatible alias for downloading an ADLS text file."""
    return read_text(service_client, file_system, path, encoding)
