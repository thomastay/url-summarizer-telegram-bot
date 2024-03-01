def bullet_point_summary(text):
    system = "You are a secretary who is reading a newspaper article, and writing a bullet point summary for your boss. He is very busy and needs to know the most important points of the article."
    instruction = f"Summarize the previous text in 5 bullet points. Each bullet point is a single sentence of around 30 words. Each sentence should be plain, at a 9th grade level. Include as many topics as possible, make every word count. Start every bullet point with a dash '-' and stop once you are done. Your bullet points should answer the 5W1H: 'Who', 'What', 'Where', 'When', 'Why' and 'How'. Example: \n- Japanese Yakuza leader accused of involvement in trafficking nuclear materials\n - Small plane carrying two people lands safely after door falls off midflight over Stiglmeier Park in Cheektowaga, New York.\n - Google apologizes after new Gemini AI refuses to show pictures, achievements of White people"
    user = f"===\n# Article\n\n{text}\n===\n{instruction}\n"
    params = {
        "temperature": 0.5,
        "max_tokens": 250,
    }
    return system, user, params


def paragraph_summary(text):
    system = "You are a secretary who is reading a newspaper article, and writing a one paragraph summary for your boss."
    instruction = f"Summarize the previous text in a single paragraph. Write at a 9th grade level. Include as many topics as possible, make every word count. Write only one single summary and stop once you are done."
    user = f"===\n# Article\n\n{text}\n===\n{instruction}\n"
    params = {
        "temperature": 0.7,
        "max_tokens": 300,
    }
    return system, user, params
