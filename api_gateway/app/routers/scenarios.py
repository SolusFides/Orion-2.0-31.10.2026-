from fastapi import APIRouter, Response, status

from app.dependencies.auth import CurrentUser
from app.repositories.scenario import ScenarioRepository
from app.schemas import scenario as schemas

router = APIRouter(prefix="/api", tags=["Scenarios"])
repo = ScenarioRepository()


@router.get("/homes/{home_id}/scenario-templates", response_model=list[schemas.TemplateOut])
async def scenario_templates(home_id: int, user: CurrentUser) -> list[schemas.TemplateOut]:
    return await repo.templates_for_home(home_id, user.id)


@router.post("/scenarios/from-template", response_model=schemas.FromTemplateOut,
             status_code=status.HTTP_201_CREATED)
async def from_template(body: schemas.FromTemplateIn, user: CurrentUser) -> schemas.FromTemplateOut:
    return await repo.create_from_template(user.id, body)


@router.get("/homes/{home_id}/scenarios", response_model=list[schemas.ScenarioOut])
async def home_scenarios(home_id: int, user: CurrentUser) -> list[schemas.ScenarioOut]:
    return await repo.list_for_home(home_id, user.id)


@router.get("/homes/{home_id}/editor-catalog", response_model=schemas.EditorCatalog)
async def editor_catalog(home_id: int, user: CurrentUser) -> schemas.EditorCatalog:
    return await repo.editor_catalog(home_id, user.id)


@router.post("/scenarios/validate", response_model=schemas.ValidateOut)
async def validate_scenario(body: schemas.ScenarioValidateIn, user: CurrentUser) -> schemas.ValidateOut:
    return await repo.validate(user.id, body)


@router.post("/scenarios", response_model=schemas.ScenarioOut, status_code=status.HTTP_201_CREATED)
async def create_scenario(body: schemas.ScenarioCreate, user: CurrentUser) -> schemas.ScenarioOut:
    return await repo.create(user.id, body)


@router.get("/scenarios/{scenario_id}", response_model=schemas.ScenarioOut)
async def get_scenario(scenario_id: int, user: CurrentUser) -> schemas.ScenarioOut:
    return await repo.get(scenario_id, user.id)


@router.put("/scenarios/{scenario_id}", response_model=schemas.ScenarioOut)
async def update_scenario(scenario_id: int, body: schemas.ScenarioBody, user: CurrentUser) -> schemas.ScenarioOut:
    return await repo.update(scenario_id, user.id, body)


@router.patch("/scenarios/{scenario_id}", response_model=schemas.ScenarioOut)
async def patch_scenario(scenario_id: int, body: schemas.ScenarioPatch, user: CurrentUser) -> schemas.ScenarioOut:
    return await repo.patch(scenario_id, user.id, body)


@router.delete("/scenarios/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario(scenario_id: int, user: CurrentUser) -> Response:
    await repo.delete(scenario_id, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
