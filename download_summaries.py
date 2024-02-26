import json
from summarizer.database import table_service_client


def download_bullet_summaries():
    # Assuming table_service_client is a global variable
    # and it's already authenticated and connected to your Azure Table Storage
    table_client = table_service_client.get_table_client("summaries")

    # Define the query to filter records where type is 'bullet_point'
    query_filter = "type eq 'bullet_point'"

    # Use a list comprehension to retrieve the records
    summaries = [
        entity
        for entity in table_client.query_entities(
            query_filter=query_filter,
            top=10,
        )
    ]

    # Save the records to summaries.json
    with open("out/summaries.json", "w") as file:
        json.dump(summaries, file, default=str)


# Call the function to download and save the records
download_bullet_summaries()
