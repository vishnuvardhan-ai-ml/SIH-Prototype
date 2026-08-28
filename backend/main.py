"""
Compatibility Entry Point for SIH Prototype Backend.
Exposes 'app' from backend.app.main for direct uvicorn execution.
"""
from backend.app.main import app

if __name__ == "__main__":
    import uvicorn
    from backend.app.core.config import settings

    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )