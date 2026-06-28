from fastapi import APIRouter

from app.api.v1.analytics.routes import router as analytics_router
from app.api.v1.auth.routes import router as auth_router
from app.api.v1.code_execution.routes import router as code_execution_router
from app.api.v1.health import router as health_router
from app.api.v1.interview.routes import router as interview_router
from app.api.v1.interview.ws_routes import router as interview_ws_router
from app.api.v1.report.routes import router as report_router
from app.api.v1.speech.routes import router as speech_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(analytics_router)
api_router.include_router(auth_router)
api_router.include_router(code_execution_router)
api_router.include_router(interview_router)
api_router.include_router(interview_ws_router)
api_router.include_router(report_router)
api_router.include_router(speech_router)
