from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response, FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
import time

# define metrics
REQUEST_COUNT = Counter(
    "request_count", "Total number of requests", ["method", "endpoint", "http_status"]
)
REQUEST_DURATION = Histogram(
    "request_duration_seconds", "Request duration in seconds", ["method", "endpoint"]
)

# define Prometheus middleware
class PrometheusMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            http_status=response.status_code,
        ).inc()

        REQUEST_DURATION.labels(
            method=request.method, endpoint=request.url.path
        ).observe(process_time)

        return response

def setup_metrics(app: FastAPI):
    app.add_middleware(PrometheusMiddleware)

    @app.get("/metrics")
    async def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

