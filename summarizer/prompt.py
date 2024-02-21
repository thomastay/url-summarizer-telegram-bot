def title_prompt(title):
    system = (
        "You are a helpful AI assistant who is an expert at predicting user questions."
    )
    user = f"The following is an article's title: `{title}`. Create three questions that a reader would have before reading this article. Your questions should be as different as possible, assuming the reader does not know anything about the topic. Be creative. Start questions with the 5W1H: 'Who', 'What', 'Where', 'When', 'Why' and 'How'. Only respond with the question, do not give an answer. Answer with a JSON object containing an array of strings. Example: {{'questions': ['What are ...', 'How is ...', 'Why did ...']}}"
    params = {
        "temperature": 1.0,
        "max_tokens": 100,
    }
    return system, user, params


def summary_with_questions(text, questions):
    system = "You are a helpful AI assistant who follows instructions to the letter. You will generate a summary of the article and answer the questions that come afterwards."
    instruction = f"First, summarize the previous text in one paragraph. Include as many topics as possible, make every word count. Create only one single summary and stop once you are done.\nThen, answer the following questions, repeating the question before the answer:\n1.{questions[0]}\n2.{questions[1]}\n3.{questions[2]}.\nExample: 1: What is the question?\nA: This is the answer."
    user = f"===\n# Article\n\n{text}\n===\n{instruction}\n"
    params = {
        "temperature": 0.7,
        "max_tokens": 400,
    }
    return system, user, params
