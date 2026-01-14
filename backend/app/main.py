from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_router

app = FastAPI(
    title="Document Verification Platform",
    description="AI-powered document verification system for Indian government services",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Document Verification Platform"}


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "components": {
            "api": "up",
            "database": "up"  # TODO: Add actual DB health check
        }
    }
