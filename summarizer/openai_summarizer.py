import json
from openai import OpenAI

from .prompt import (
    summary_with_questions,
    title_prompt,
)
import os

env = os.environ.get("ENV")

client = OpenAI()
questions_model = "gpt-4-turbo-preview"
if env == "development":
    questions_model = "gpt-3.5-turbo-0125"
summary_model = "gpt-3.5-turbo-0125"


def questions_from_title(title):
    system, user, params = title_prompt(title)
    questions = completions(
        model=questions_model,
        system=system,
        user=user,
        max_tokens=params["max_tokens"],
        temperature=params["temperature"],
        is_json=True,
    )
    questions_json = json.loads(questions)
    questions_arr = questions_json["questions"]
    return questions_arr


def summarize_openai(text, questions):
    system, user, params = summary_with_questions(text, questions)
    yield from completions_stream(
        model=summary_model,
        system=system,
        user=user,
        max_tokens=params["max_tokens"],
        temperature=params["temperature"],
        is_json=False,
    )


def summarize_openai_sync(text, questions):
    system, user, params = summary_with_questions(text, questions)
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
