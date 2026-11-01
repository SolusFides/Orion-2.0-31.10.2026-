from fastapi import APIRouter, Query, Response, status

from app.dependencies.auth import CurrentUser
from app.repositories.device import DeviceRepository, DeviceTypeRepository
from app.schemas import device as schemas

router = APIRouter(prefix="/api", tags=["Devices"])
repo = DeviceRepository()
types_repo = DeviceTypeRepository()


@router.get("/device-types", response_model=list[schemas.DeviceTypeOut])
async def device_types(_: CurrentUser) -> list[schemas.DeviceTypeOut]:
    return await repo.list_types()


@router.get("/device-types/{type_id}", response_model=schemas.DeviceTypeDetail)
async def get_device_type(type_id: int, _: CurrentUser) -> schemas.DeviceTypeDetail:
    return await types_repo.get(type_id)


@router.post("/device-types", response_model=schemas.DeviceTypeDetail, status_code=status.HTTP_201_CREATED)
async def create_device_type(body: schemas.DeviceTypeIn, _: CurrentUser) -> schemas.DeviceTypeDetail:
    return await types_repo.create(body)


@router.put("/device-types/{type_id}", response_model=schemas.DeviceTypeDetail)
async def update_device_type(type_id: int, body: schemas.DeviceTypeIn, _: CurrentUser) -> schemas.DeviceTypeDetail:
    return await types_repo.update(type_id, body)


@router.delete("/device-types/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device_type(type_id: int, _: CurrentUser) -> Response:
    await types_repo.delete(type_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/device-types/{type_id}/clone", response_model=schemas.DeviceTypeDetail,
             status_code=status.HTTP_201_CREATED)
async def clone_device_type(type_id: int, body: schemas.CloneIn, _: CurrentUser) -> schemas.DeviceTypeDetail:
    return await types_repo.clone(type_id, body)


@router.post("/devices", response_model=schemas.DeviceOut, status_code=status.HTTP_201_CREATED)
async def create_device(body: schemas.DeviceCreate, user: CurrentUser) -> schemas.DeviceOut:
    return await repo.create(user.id, body)


@router.get("/devices/{device_id}", response_model=schemas.DeviceOut)
async def get_device(device_id: int, user: CurrentUser) -> schemas.DeviceOut:
    return await repo.get(device_id, user.id)


@router.patch("/devices/{device_id}", response_model=schemas.DeviceOut)
async def patch_device(device_id: int, body: schemas.DevicePatch, user: CurrentUser) -> schemas.DeviceOut:
    return await repo.patch(device_id, user.id, body)


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(device_id: int, user: CurrentUser) -> Response:
    await repo.delete(device_id, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/devices/{device_id}/commands", response_model=schemas.CommandResult)
async def send_command(device_id: int, body: schemas.CommandIn, user: CurrentUser) -> schemas.CommandResult:
    return await repo.command(device_id, user.id, body)


@router.get("/devices/{device_id}/commands", response_model=list[schemas.CommandOut])
async def list_commands(device_id: int, user: CurrentUser,
                        limit: int = Query(50, ge=1, le=200)) -> list[schemas.CommandOut]:
    return await repo.commands(device_id, user.id, limit)


@router.post("/devices/{device_id}/simulate", response_model=schemas.SimulateOut)
async def simulate(device_id: int, body: schemas.SimulateIn, user: CurrentUser) -> schemas.SimulateOut:
    return await repo.simulate(device_id, user.id, body)


@router.post("/devices/{device_id}/simulate/online", response_model=schemas.OnlineOut)
async def simulate_online(device_id: int, body: schemas.OnlineIn, user: CurrentUser) -> schemas.OnlineOut:
    return await repo.set_online(device_id, user.id, body.online)
