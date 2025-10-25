# _5_agents.py
import os
import openai
from _4_rag import RAG

openai.api_key = os.getenv('GROQ_API_KEY')

rag = RAG()

class DataExtractor:
    def specs(self, model_name):
        return rag.get_specs(model_name)

    def compare_specs(self, a, b):
        a_specs = rag.get_specs(a)
        b_specs = rag.get_specs(b)
        return a_specs, b_specs

    def best_battery_under(self, price_limit):
        return rag.find_best_battery_under(price_limit)


class ReviewGenerator:
    def __init__(self, model_name='llama-3.1-8b-instant'):
        self.model_name = model_name

    def generate_comparison(self, a_name, a_specs, b_name, b_specs, focus=None):
        # Build a structured prompt for the LLM
        prompt = "You are a helpful tech reviewer. Compare two Samsung phone models."
        prompt += f"\nModel A: {a_name}\nSpecs: {a_specs}\n\nModel B: {b_name}\nSpecs: {b_specs}\n"
        if focus:
            prompt += f"Focus the comparison on {focus}.\n"
        prompt += "Give a concise conclusion and recommendation. Use plain language."

        response = openai.ChatCompletion.create(
            model='llama-3.1-8b-instant',
            messages=[
                        {"role": "system", "content": "You are a phone review assistant."},
                        {"role": "user", "content": prompt}
                    ],
            max_tokens=300,
            temperature=0.2,
        )
        text = response['choices'][0]['message']['content'].strip()
        return text

    def generate_recommendation_from_list(self, phones_list, criteria='battery'):
        prompt = f"You are a helpful tech reviewer. Given this list of phones and their specs, recommend the best one based on {criteria}.\n\n"
        prompt += str(phones_list)
        prompt += "\nGive a short recommendation and reason."
        response = openai.ChatCompletion.create(
            model='llama-3.1-8b-instant',
            messages=[{"role":"user","content":prompt}],
            max_tokens=200,
            temperature=0.2
        )
        return response['choices'][0]['message']['content']