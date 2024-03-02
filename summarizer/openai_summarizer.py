from typing import Tuple
from openai import OpenAI
import logging

from .text import MAX_CHUNK_LENGTH, split_text
from .prompt import bullet_point_summary, paragraph_summary
import os

env = os.environ.get("ENV")

client = OpenAI(
    base_url="https://mixtral-8x7b.lepton.run/api/v1/",
    api_key=os.environ.get("LEPTON_API_KEY"),
)
summary_model = "mixtral-8x7b:lepton"


def summarize_openai_stream(text):
    system, user, params = bullet_point_summary(text)
    yield from completions_stream(
        model=summary_model,
        system=system,
        user=user,
        max_tokens=params["max_tokens"],
        temperature=params["temperature"],
        is_json=False,
    )


def summarize_openai_sync(text: str) -> dict:
    if len(text) <= MAX_CHUNK_LENGTH:
        logging.info("Sending bullet point summary request to OpenAI")
        system, user, params = bullet_point_summary(text)
        summary = completions(
            model=summary_model,
            system=system,
            user=user,
            max_tokens=params["max_tokens"],
            temperature=params["temperature"],
            is_json=False,
        )
        summary_info = {
            "summary": summary,
            "model": summary_model,
            "type": "bullet_point",
        }
        return summary_info

    # Text is too long, split it into chunks
    chunks = split_text(text)
    logging.info(
        f"Text is too long at {len(text)} chars. Splitting into {len(chunks)} chunks and summarizing each chunk first."
    )
    # We summarize each chunk into a paragraph summary first.
    # Then, we take all those paragraphs and turn them into a bullet point summary.
    # TODO change this to async and use Promises to execute all summaries at once
    summaries = []
    for i, chunk in enumerate(chunks):
        system, user, params = paragraph_summary(chunk)
        para_summary = completions(
            model=summary_model,
            system=system,
            user=user,
            max_tokens=params["max_tokens"],
            temperature=params["temperature"],
            is_json=False,
        )
        logging.info(f"Completed summary {i+1} of {len(chunks)}")
        summaries.append(para_summary)
    # Now we have a list of paragraph summaries. We turn them into a bullet point summary.
    logging.info("Sending bullet point summary request to OpenAI")
    system, user, params = bullet_point_summary("\n".join(summaries))
    summary = completions(
        model=summary_model,
        system=system,
        user=user,
        max_tokens=params["max_tokens"],
        temperature=params["temperature"],
        is_json=False,
    )
    summary_info = {
        "summary": summary,
        "model": summary_model,
        "type": "bullet_point_chunked",
        "paragraph_summaries": summaries,
    }
    return summary_info


def completions_stream(
    model,
    system,
    user,
    max_tokens,
    temperature,
    is_json,
):
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    response_format = {"type": "json_object"} if is_json else None
    stream = client.chat.completions.create(
        model=model,
        response_format=response_format,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        stream=True,
    )
    partial_message: str = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            partial_message += str(chunk.choices[0].delta.content)
            yield partial_message


def completions(
    model,
    system,
    user,
    max_tokens,
    temperature,
    is_json,
):
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    response_format = {"type": "json_object"} if is_json else None
    completion = client.chat.completions.create(
        model=model,
        response_format=response_format,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        stream=False,
    )
    return completion.choices[0].message.content
