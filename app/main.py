from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routes import payroll
from app.database.connection import Base,async_engine
from prometheus_fastapi_instrumentator import Instrumentator



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # Application is now running
    print("App shutdown complete!")
    # (Optional) Shutdown logic here if needed
    # e.g. await some_cleanup()


# Initialize FastAPI app
app = FastAPI(
    title="Global Payroll Microservice",
    version="1.0.0",
    description="Modular FastAPI payroll service with Gross-to-Net calculations across countries."
)

        
# Monitoring (Prometheus metrics exposed at /metrics)
Instrumentator().instrument(app).expose(app)

# Include API routes
app.include_router(payroll.router)