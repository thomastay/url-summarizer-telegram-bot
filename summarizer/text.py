import math
import trafilatura
import logging
from lxml import html
from typing import List


def extract_title(html_str):
    # Assuming you have a string 'html_str' containing the HTML content
    html_content = html_str

    # Parse the HTML content
    tree = html.fromstring(html_content)

    # Use xpath to select the <title> element in the <head> element
    title_element = tree.xpath("//head/title")

    # If the <title> element is found, print its text
    if title_element:
        return title_element[0].text

    # try to find title element anywhere else
    title_element = tree.xpath(".//title")
    if title_element:
        return title_element[0].text

    logging.warning("No <title> element found in the <head> element.")
    return None


def get_text(url):
    downloaded = trafilatura.fetch_url(url)
    prune_xpath = ["//code", "//pre"]

    return trafilatura.extract(
        downloaded,
        prune_xpath=prune_xpath,
        include_tables=False,
    )


def get_text_and_title(url):
    downloaded = trafilatura.fetch_url(url)
    title = extract_title(downloaded)
    prune_xpath = ["//code", "//pre"]
    text = trafilatura.extract(
        downloaded,
        prune_xpath=prune_xpath,
        include_tables=False,
    )
    return title, text


APPROX_CHARS_PER_TOKEN = 4
MAX_TOKEN_LENGTH_PER_SUMMARY = 8192
MAX_CHUNK_LENGTH = MAX_TOKEN_LENGTH_PER_SUMMARY * APPROX_CHARS_PER_TOKEN


def split_text(text: str, max_length=MAX_CHUNK_LENGTH) -> List[str]:
    total_length = len(text)
    if total_length <= max_length:
        return [text]

    paragraphs = text.split("\n")

    # Check if there are at least two paragraphs for splitting
    if len(paragraphs) < 2:
        return [text]

    # We try to split as evenly as possible
    target_num_chunks = math.ceil(total_length / max_length)
    target_length = math.ceil(total_length / target_num_chunks)
    logging.debug(
        f"Splitting into {target_num_chunks} chunks of length {target_length}."
    )
    result = []
    curr = 0
    current_length = 0
    for i, paragraph in enumerate(paragraphs):
        current_length += len(paragraph)
        if current_length >= target_length:
            result.append("\n".join(paragraphs[curr:i]))
            curr = i
            current_length = 0

    # Finalize the last chunk
    if curr < len(paragraphs):
        result.append("\n".join(paragraphs[curr:]))
    return result
