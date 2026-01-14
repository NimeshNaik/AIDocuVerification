from fastapi import APIRouter

from app.api.v1.endpoints import auth, verify, audit, documents

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(verify.router)
router.include_router(audit.router)
router.include_router(documents.router)
