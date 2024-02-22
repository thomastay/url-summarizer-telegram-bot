import trafilatura
from lxml import html


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

    print("No <title> element found in the <head> element.")
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
