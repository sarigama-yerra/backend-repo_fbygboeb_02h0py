import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None


class ChatResponse(BaseModel):
    reply: str


def generate_reply(message: str, history: Optional[List[ChatMessage]] = None) -> str:
    """A lightweight, rule-based chatbot to keep the demo self-contained."""
    text = message.strip().lower()

    # Small intents
    if any(greet in text for greet in ["hello", "hi", "hey"]):
        return "Hi! I'm your helpful AI. Ask me anything or try: 'summarize this text', 'write a haiku about the ocean', or 'explain JWTs like I'm five'."
    if "your name" in text or "who are you" in text:
        return "I'm an on-device AI assistant built for this demo. No external services required!"
    if "help" in text:
        return "I can answer questions, brainstorm ideas, rewrite text, draft emails, and more. What would you like to do?"
    if "time" in text and "?" in text:
        from datetime import datetime
        return f"It's {datetime.utcnow().strftime('%H:%M UTC on %Y-%m-%d')}"

    # Simple transformations
    if text.startswith("summarize "):
        body = message[len("summarize ") :].strip()
        if len(body) < 10:
            return "Please paste some text after 'summarize' for me to condense."
        sentences = [s.strip() for s in body.replace("\n", " ").split(".") if s.strip()]
        return (
            "Summary: "
            + ("; ".join(sentences[:3]))
            + ("..." if len(sentences) > 3 else "")
        )

    if text.startswith("rewrite ") or text.startswith("paraphrase "):
        body = message.split(" ", 1)[1]
        return f"Here's a clearer version: {body.capitalize()}"

    if "haiku" in text:
        return "Ocean whispers soft\nSilver tides kiss moonlit sands\nDreams drift with the stars"

    if any(x in text for x in ["joke", "funny"]):
        return "Why did the developer go broke? Because they used up all their cache."

    # If there's history, reflect lightly
    if history:
        last_user = next((m.content for m in reversed(history) if m.role == "user"), None)
        if last_user and last_user != message:
            return (
                "Following up on our chat: you previously asked '"
                + last_user[:120]
                + ("..." if len(last_user) > 120 else "")
                + "'. Now, about your new message — here's my best take: "
                + message
            )

    # Default assistant behavior
    return (
        "Here's a thoughtful response: I understand you're asking about '"
        + message.strip()[:140]
        + ("..." if len(message.strip()) > 140 else "")
        + "'. I can provide explanations, examples, or step-by-step guidance — just tell me the depth you want."
    )


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    reply = generate_reply(req.message, req.history)
    return ChatResponse(reply=reply)


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
