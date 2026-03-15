from fastapi import FastAPI
from pydantic import BaseModel

# Initialize the FastAPI app
app = FastAPI(
    title="DA-IICT RAG API",
    description="Backend API for the DA-IICT RAG Chatbot",
    version="1.0.0"
)

# Minimal request model for future testing
class QueryRequest(BaseModel):
    query: str

@app.get("/health")
async def health_check():
    """
    Used by Docker Compose to verify the API container is running and responsive.
    """
    return {"status": "healthy", "service": "api"}

@app.post("/api/v1/query")
async def query_endpoint(request: QueryRequest):
    """
    Placeholder endpoint for Phase 2. 
    Eventually, this will trigger the embedding search and LLM generation.
    """
    return {
        "answer": f"Echo: I received your query about '{request.query}', but the RAG pipeline is not built yet!",
        "sources": []
    }