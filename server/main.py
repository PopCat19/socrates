# main.py
#
# Purpose: FastAPI server exposing Socrates API and serving the production web UI
#
# This module:
# - Proxies model listing from the configured LLM backend
# - Generates clarifying questions via POST /api/questions
# - Streams extended reasoning responses via POST /api/submit

import json
import os
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.llm_client import LLMClient
from shared.prompt import EXTENDED_SYSTEM, get_questions

PORT = int(os.getenv("PORT", 7384))
WEB_DIST = Path(__file__).parent.parent / "web" / "dist"

app = FastAPI(title="Socrates")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
client = LLMClient()


class QuestionRequest(BaseModel):
    prompt: str
    model: str


class SubmitRequest(BaseModel):
    prompt: str
    model: str


@app.get("/api/models")
async def list_models():
    return {"models": await client.list_models()}


@app.post("/api/questions")
async def generate_questions(req: QuestionRequest):
    questions = await get_questions(client, req.prompt, req.model)
    return {"questions": [{"priority": q.priority, "question": q.question} for q in questions]}


@app.post("/api/submit")
async def submit(req: SubmitRequest):
    messages = [
        {"role": "system", "content": EXTENDED_SYSTEM},
        {"role": "user", "content": req.prompt},
    ]

    async def sse():
        async for token in client.stream_complete(messages, req.model):
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(sse(), media_type="text/event-stream")


if WEB_DIST.exists():
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="static")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
