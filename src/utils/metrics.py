from prometheus_client import Counter, Gauge, Histogram, generate_latest,CONTENT_TYPE_LATEST
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from time import time

#Define Metrics
REQUEST_COUNT = Counter("http_request_total", "HTTP Requests",["method", "endpoint","status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP Request Latency",["method", "endpoint"])




class PrometheusMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start_time = time()
        response = await call_next(request)
        process_time = time() - start_time
        endpoint=request.url.path
        REQUEST_COUNT.labels(request.method, endpoint, response.status_code).inc()
        REQUEST_LATENCY.labels(request.method, endpoint).observe(process_time)

        return response


def setup_metrics(app: FastAPI):
    app.add_middleware(PrometheusMiddleware)

    @app.get("/TrhBVer",include_in_schema=False)
    async def metrics():
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
    
    