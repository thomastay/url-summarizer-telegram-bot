import asyncio
from aiolimiter import AsyncLimiter
from openai import AsyncOpenAI
import logging

from .text import MAX_CHUNK_LENGTH, split_text
from .prompt import bullet_point_summary, paragraph_summary
import os

env = os.environ.get("ENV")

client = AsyncOpenAI(
    base_url="https://mixtral-8x7b.lepton.run/api/v1/",
    api_key=os.environ.get("LEPTON_API_KEY"),
)
summary_model = "mixtral-8x7b:lepton"
# 10 reqs per min, see https://www.lepton.ai/docs/overview/model_apis
rate_limit = AsyncLimiter(10, 60)


async def summarize_openai(text: str) -> dict:
    if len(text) <= MAX_CHUNK_LENGTH:
        logging.info("Sending bullet point summary request to OpenAI")
        system, user, params = bullet_point_summary(text)
        summary = await completions(
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
    summaries_tasks = [summarize_chunk(i, chunk) for i, chunk in enumerate(chunks)]
    summaries = await asyncio.gather(*summaries_tasks)

    # Now we have a list of paragraph summaries. We turn them into a bullet point summary.
    logging.info("Sending bullet point summary request to OpenAI")
    system, user, params = bullet_point_summary("\n".join(summaries))
    summary = await completions(
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


async def summarize_chunk(i: int, chunk: str):
    system, user, params = paragraph_summary(chunk)
    res = await completions(
        model=summary_model,
        system=system,
        user=user,
        max_tokens=params["max_tokens"],
        temperature=params["temperature"],
        is_json=False,
    )
    logging.info(f"Completed summarizing chunk {i}")
    return res


async def completions(
    model,
    system,
    user,
    max_tokens,
    temperature,
    is_json,
):
    # Rate limit
    async with rate_limit:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        response_format = {"type": "json_object"} if is_json else None
        completion = await client.chat.completions.create(
            model=model,
            response_format=response_format,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=False,
        )
        return completion.choices[0].message.content
