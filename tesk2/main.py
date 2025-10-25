# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents import DataExtractor, ReviewGenerator
import re

app = FastAPI(title='Samsung Phone Advisor')

data_agent = DataExtractor()
review_agent = ReviewGenerator()

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    sources: list | None = None


def parse_question(q: str):
    q_low = q.lower()
    # simple heuristics
    # 1) Compare X and Y
    m = re.search(r'compare\s+(.*?)\s+and\s+(.*)', q_low)
    if m:
        return {'intent': 'compare', 'a': m.group(1).strip(), 'b': m.group(2).strip()}
    # 2) Specs of Model
    m2 = re.search(r'specs\s+of\s+(.*)', q_low)
    if m2:
        return {'intent': 'specs', 'model': m2.group(1).strip()}
    # 3) Best battery under $X
    m3 = re.search(r'best.*battery.*under\s*\$?(\d+)', q_low)
    if m3:
        return {'intent': 'best_battery', 'price': float(m3.group(1))}
    # fallback
    return {'intent': 'general', 'q': q}


@app.post('/ask', response_model=AskResponse)
async def ask(req: AskRequest):
    parsed = parse_question(req.question)

    if parsed['intent'] == 'specs':
        specs = data_agent.specs(parsed['model'])
        if not specs:
            raise HTTPException(status_code=404, detail='Model not found')
        # build answer text
        p = specs[0]
        answer = f"{p['model_name']} has {p['display']}, {p['battery']}mAh battery, camera: {p['camera']}, RAM: {p['ram']}, storage: {p['storage']}."
        return {'answer': answer, 'sources': [p['source_url']]}

    if parsed['intent'] == 'compare':
        a_raw = parsed['a']
        b_raw = parsed['b']
        a_specs = data_agent.specs(a_raw)
        b_specs = data_agent.specs(b_raw)
        if not a_specs or not b_specs:
            raise HTTPException(status_code=404, detail='One or both models not found')
        # use review agent
        text = review_agent.generate_comparison(a_specs[0]['model_name'], a_specs[0], b_specs[0]['model_name'], b_specs[0])
        # compose a short facts section
        facts = f"Facts:\n{a_specs[0]['model_name']}: {a_specs[0]['display']}, {a_specs[0]['battery']}mAh.\n{b_specs[0]['model_name']}: {b_specs[0]['display']}, {b_specs[0]['battery']}mAh."
        answer = facts + "\n\nReview:\n" + text
        sources = [a_specs[0]['source_url'], b_specs[0]['source_url']]
        return {'answer': answer, 'sources': sources}

    if parsed['intent'] == 'best_battery':
        found = data_agent.best_battery_under(parsed['price'])
        if not found:
            raise HTTPException(status_code=404, detail='No phone found under that price with battery info')
        ans = f"{found['model_name']} has the largest battery under ${parsed['price']}: {found['battery']} mAh (price: ${found['price_usd']})."
        return {'answer': ans, 'sources': [found['source_url']]}

    # fallback: try to answer general queries by searching models for names
    return {'answer': "Sorry — I couldn't interpret that question. Try: 'Specs of <model>', 'Compare <A> and <B>', or 'Best battery under $X'.", 'sources': None}