from fastapi import FastAPI, HTTPException
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
    try:
        think, answer, interaction = generate(request.message)
        return {"message": answer, "thinking": think, "interaction": interaction}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    load_dotenv()
    PORT = int(os.getenv("AI_PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT
    )