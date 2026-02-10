# workflows/middleware.py
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("codegen")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

async def add_logging_middleware(request: Request, call_next):
    logger.info(f"Incoming {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code} for {request.url.path}")
        return response
    except Exception as e:
        logger.exception("Unhandled exception while processing request")
        return JSONResponse(status_code=500, content={"error": "Internal server error"})
