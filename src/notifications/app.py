from fastapi import FastAPI

from .health import router as health_router
from .routes import router as notifications_router

app = FastAPI(
    title="Notification API",
    version="1.0.0",
    description=(
        "Reference Python notification API — "
        "event compatibility, PII controls, factory reuse proof"
    ),
    docs_url="/docs",
    redoc_url=None,
)

app.include_router(notifications_router)
app.include_router(health_router)


if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run(
        "src.notifications.app:app",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "3003")),
        reload=False,
    )
