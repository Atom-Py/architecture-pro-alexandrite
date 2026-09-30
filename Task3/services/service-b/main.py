"""service-b: сервис расчёта стоимости.

GET / считает стоимость заказа. Входящий заголовок traceparent
продолжает трейс service-a.
"""

import random
import time

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Имя сервиса и адрес коллектора берутся из OTEL_SERVICE_NAME
# и OTEL_EXPORTER_OTLP_ENDPOINT
provider = TracerProvider(resource=Resource.create())
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

app = FastAPI(title="service-b")
FastAPIInstrumentor.instrument_app(app)


@app.get("/")
def calculate_price(order_id: int = 0):
    with tracer.start_as_current_span("calculate price") as span:
        polygons = random.randint(10_000, 500_000)
        span.set_attribute("order.id", order_id)
        span.set_attribute("model.polygons", polygons)
        # расчёт занимает время пропорционально сложности модели
        time.sleep(polygons / 5_000_000)
        price = round(polygons * 0.05, 2)
        span.set_attribute("price.calculation.result", "success")
    return {"order_id": order_id, "polygons": polygons, "price": price}
