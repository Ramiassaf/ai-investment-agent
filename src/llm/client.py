import os 
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_answer(system_prompt: str, user_prompt: str, model: str | None = None) -> str:
    resolved_model = model or os.getenv("OPENAI_MODEL")
    if not resolved_model:
        raise ValueError("No model specified. Set OPENAI_MODEL in your .env file.")
    resp = client.chat.completions.create(
        model=resolved_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()


