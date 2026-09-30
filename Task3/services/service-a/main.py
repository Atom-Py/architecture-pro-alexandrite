"""service-a: сервис заказов.

GET / отдаёт заказ и за стоимостью обращается в service-b.
Контекст трейса передаётся в service-b заголовком traceparent,
поэтому оба сервиса попадают в один трейс.
"""

import os
import random

import httpx
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

SERVICE_B_URL = os.getenv("SERVICE_B_URL", "http://service-b:8080")

# Имя сервиса и адрес коллектора берутся из OTEL_SERVICE_NAME
# и OTEL_EXPORTER_OTLP_ENDPOINT
provider = TracerProvider(resource=Resource.create())
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

app = FastAPI(title="service-a")
FastAPIInstrumentor.instrument_app(app)
HTTPXClientInstrumentor().instrument()


@app.get("/")
def get_order():
    order_id = random.randint(10000, 99999)
    with tracer.start_as_current_span("get order") as span:
        span.set_attribute("order.id", order_id)
        span.set_attribute("order.status", "SUBMITTED")
        response = httpx.get(SERVICE_B_URL, params={"order_id": order_id}, timeout=5)
        response.raise_for_status()
        price = response.json()
        span.set_attribute("order.price", price["price"])
    return {"order_id": order_id, "status": "SUBMITTED", "price": price}
