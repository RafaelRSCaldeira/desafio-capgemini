from fastapi import FastAPI
import uvicorn
from dotenv import load_dotenv
import os
from pydantic import BaseModel

from src.agent.agent import generate

app = FastAPI()

class Request(BaseModel):
    message: str

@app.get("/ai/health/")
def health():
    return {"status": 201}

@app.post("/ai/generate/")
def generate_(request: Request):
    response = generate(request.message)
    return {"message": response.content}

if __name__ == "__main__":
    load_dotenv()
    PORT = int(os.getenv("AI_PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT
    )