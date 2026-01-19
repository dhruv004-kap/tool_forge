import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

def get_accuracy(text):
    pattern = re.compile(r"(\d+\.\d+)%")

    result = re.search(pattern, text)
    if result:
        accuracy = result.group(1)
        return accuracy
    else:
        return 0

def evaluate_prompt(prompt):
    prompt_evaluator_url = os.getenv("PROMPT_EVALUATOR_URL")

    body = {
        "evaluate_target": "assistant",
        "input_text": prompt
    }

    response = requests.post(url=prompt_evaluator_url, json=body)
    response.raise_for_status

    res_json = response.json()
    prompt_text = res_json.get("output_text")

    prompt_accuracy = get_accuracy(prompt_text)

    return {
        "prompt": prompt,
        "accuracy": prompt_accuracy
    }