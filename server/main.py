from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth.routes import router as auth_router
from docs.routes import router as docs_router
from chat.routes import router as chat_router

app = FastAPI(
    title="Healthcare RBAC Assistant API",
    description="RAG-based healthcare assistant with role-based access control",
    version="1.0.0"
)

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this with proper origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(docs_router)
app.include_router(chat_router)


@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Healthcare RBAC API is running"}


@app.get("/")
def root():
    return {"message": "Healthcare RBAC RAG Assistant API", "docs": "/docs"}

