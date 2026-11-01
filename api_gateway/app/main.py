import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import assistant, auth, demo, devices, homes, meta, notifications, runs, scenarios, ujin
from app.services import errors
from app.services.emulator import emulator
from app.services.engine import engine
from app.services.ujin import publisher

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await engine.start()
    await emulator.start()
    await publisher.start()
    yield
    for part in (publisher, emulator, engine):
        await part.stop()


app = FastAPI(
    title="Orion Home API",
    description="API for the Ujin OS smart home scenario editor: devices, emulators, scenarios and automation.",
    version="0.4.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)
errors.install(app)

for r in (auth.router, meta.router, homes.router, devices.router, scenarios.router, runs.router,
          notifications.router, assistant.router, ujin.router, demo.router):
    app.include_router(r)
