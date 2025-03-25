from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import json

logger = logging.getLogger(__name__)

class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Define allowed origins
        allowed_origin = "http://localhost:5173"
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            logger.info("Handling OPTIONS preflight request")
            headers = {
                "Access-Control-Allow-Origin": allowed_origin,
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Max-Age": "86400",  # 24 hours
            }
            return Response(status_code=200, headers=headers)
        
        try:
            # Process the request
            logger.info(f"Processing {request.method} request to {request.url.path}")
            response = await call_next(request)
            
            # Add CORS headers to the response
            response.headers["Access-Control-Allow-Origin"] = allowed_origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            
            return response
        except Exception as e:
            # Log the error
            logger.error(f"Error processing request: {str(e)}")
            
            # Create a response with CORS headers
            error_response = {
                "detail": str(e),
                "status": "error"
            }
            
            headers = {
                "Access-Control-Allow-Origin": allowed_origin,
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
                "Access-Control-Allow-Credentials": "true",
                "Content-Type": "application/json"
            }
            
            return Response(
                content=json.dumps(error_response).encode("utf-8"),
                status_code=500,
                headers=headers
            ) 