from fastapi import FastAPI
from pydantic import BaseModel
from src.llm.answer import answer_question


app = FastAPI()

class AskRequest(BaseModel):
    question: str
    days : int = 30

class AskResponse(BaseModel):
    question: str
    answer: str
    gold_bias: str
    silver_bias: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    result =answer_question(request.question)
    return AskResponse(**result)