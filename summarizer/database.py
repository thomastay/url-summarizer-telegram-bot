import logging
import os
import hashlib
import json
from datetime import datetime
from azure.data.tables import TableServiceClient
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError


def hash_token(token: str):
    return hashlib.sha256(token.encode()).hexdigest()


blob_connection_string = os.getenv("AzureWebJobsStorage")


def init_table_service_client(connection_string) -> TableServiceClient | None:
    if connection_string is None or connection_string == "":
        logging.warning("No connection string found. Skipping database initialization.")
        return None
    return TableServiceClient.from_connection_string(connection_string)


def init_blob_service_client(connection_string) -> BlobServiceClient | None:
    if connection_string is None or connection_string == "":
        logging.warning("No connection string found. Skipping database initialization.")
        return None
    return BlobServiceClient.from_connection_string(connection_string)


table_service_client: TableServiceClient = init_table_service_client(
    blob_connection_string
)
blob_service_client: BlobServiceClient = init_blob_service_client(
    blob_connection_string
)
summaries_table_client = None
users_table_client = None
invite_codes_table_client = None
articles_container_client = None
if table_service_client is not None:
    summaries_table_client = table_service_client.get_table_client("summaries")
    users_table_client = table_service_client.get_table_client("users")
    invite_codes_table_client = table_service_client.get_table_client("invitecodes")
    articles_container_client = blob_service_client.get_container_client("articles")


def create_article(url: str, text: str) -> None:
    if articles_container_client is None:
        logging.error("No articles container client found")
        return
    url_hashed = hash_token(url)
    blob_client = articles_container_client.get_blob_client(url_hashed)
    value = {
        "url": url,
        "text": text,
    }
    blob_client.upload_blob(json.dumps(value), overwrite=True)


def read_article(url: str):
    if articles_container_client is None:
        logging.error("No articles container client found")
        return
    url_hashed = hash_token(url)

    try:
        # Attempt to get the blob client for the 'url_hashed' blob
        blob_client = articles_container_client.get_blob_client(url_hashed)

        # Try to download the blob's content
        blob_content = blob_client.download_blob().readall()

        # If the blob exists and content is successfully downloaded, return the content
        entity = json.loads(blob_content)
        return entity
    except ResourceNotFoundError:
        # If the blob does not exist, log the error and return None
        logging.info(f"The blob for {url} does not exist in the 'articles' container.")
        return None
    except Exception as e:
        # For any other exception, log the error and raise the exception
        logging.error(
            f"An error occurred while trying to access the blob for {url}: {e}"
        )
        raise


def create_summary(value: dict):
    if summaries_table_client is None:
        logging.error("No summaries table client found")
        return
    # YYYY-MM-DD as a partition key
    now = datetime.now()
    partition_key = now.strftime("%Y-%m-%d")
    ## HH:MM:SS:ms as a row key
    row_key = now.strftime("%H:%M:%S:%f")

    value["PartitionKey"] = partition_key
    value["RowKey"] = row_key

    summaries_table_client.create_entity(entity=value)


def create_user(user_id: int, invite_code: str, user_fullname: str) -> bool:
    if users_table_client is None:
        logging.error("No users table client found")
        return

    # User ids arent related to one another, so there isn't really a good way to partition them other than by hash
    partition_key = str(user_id)
    row_key = str(user_id)  # TODO: check if user_id contains invalid characters

    value = {
        "PartitionKey": partition_key,
        "RowKey": row_key,
        "user_id": user_id,
        "user_fullname": user_fullname,
        "invite_code": hash_token(invite_code),
    }

    try:
        result = users_table_client.create_entity(entity=value)
        return False
    except ResourceExistsError as e:
        logging.warning("user already exists")
        return True


def read_user(user_id: int) -> dict | None:
    if users_table_client is None:
        logging.warning("No users table client found")
        return

    partition_key = str(user_id)
    row_key = str(user_id)  # TODO: check if user_id contains invalid characters

    try:
        result = users_table_client.get_entity(partition_key, row_key)
        return result
    except Exception as e:
        logging.info(f"No such user: {e}")
        return None


def is_user_authorized(user_id: int) -> bool:
    return read_user(user_id) is not None


def is_valid_invite_code(invite_code: str) -> bool:
    if invite_codes_table_client is None:
        logging.warning("No invite codes table client found")
        return True  # only for local dev

    partition_key = hash_token(invite_code)
    row_key = hash_token(invite_code)
    try:
        invite_codes_table_client.get_entity(partition_key, row_key)
        return True
    except Exception as e:
        logging.error(f"Could not read entity: {e}")
        return False


def create_invite_code(invite_code: str):
    if invite_codes_table_client is None:
        logging.error("No invite codes table client found")
        return

    partition_key = hash_token(invite_code)
    row_key = hash_token(invite_code)

    value = {
        "PartitionKey": partition_key,
        "RowKey": row_key,
    }

    result = invite_codes_table_client.create_entity(entity=value)
