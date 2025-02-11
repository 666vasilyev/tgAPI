# uvicorn main:app --host 0.0.0.0 --port 8000 --reload
from fastapi import FastAPI


from src.routes.account import router as account_router
from src.routes.proxy import router as proxy_router
from src.routes.report import router as report_router
from src.routes.task import router as task_router


def get_app() -> FastAPI:

    app = FastAPI(
        title="Logistics App", 
        description="An app to manage objects, chains, categories, and products.",
    )
    

    # Include routers
    app.include_router(account_router, prefix="/account", tags=["Accounts"])
    app.include_router(proxy_router, prefix="/proxy", tags=["Proxies"])
    app.include_router(report_router, prefix="/report", tags=["Reports"])

    app.include_router(task_router, prefix="/task", tags=["tasks"])

    return app