from openai import OpenAI

from .prompt import bullet_point_summary
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


def summarize_openai_sync(text):
    system, user, params = bullet_point_summary(text)
    return completions(
        model=summary_model,
        system=system,
        user=user,
        max_tokens=params["max_tokens"],
        temperature=params["temperature"],
        is_json=False,
    )


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
