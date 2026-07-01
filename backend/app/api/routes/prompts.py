from fastapi import APIRouter, HTTPException

from app.ai.registry import list_available_judges, list_available_models
from app.prompts.templates import PromptTemplateManager
from app.schemas.api import PromptResponse, PromptUpdate

router = APIRouter(tags=["prompts", "models"])

prompt_manager = PromptTemplateManager()


@router.get("/prompts", response_model=list[PromptResponse])
async def list_prompts():
    return prompt_manager.list_templates()


@router.get("/prompts/{name}", response_model=PromptResponse)
async def get_prompt(name: str):
    template = prompt_manager.get_template(name)
    if not template:
        raise HTTPException(404, "Prompt template not found")
    return PromptResponse(
        name=template.name,
        version=template.version,
        description=template.description,
        template=template.template,
        created_at=template.created_at.isoformat(),
    )


@router.put("/prompts/{name}", response_model=PromptResponse)
async def update_prompt(name: str, data: PromptUpdate):
    pv = prompt_manager.update_template(name, data.template, data.version, data.description)
    return PromptResponse(
        name=pv.name,
        version=pv.version,
        description=pv.description,
        template=pv.template,
        created_at=pv.created_at.isoformat(),
    )


@router.get("/models")
async def list_models():
    return {
        "models": list_available_models(),
        "judges": list_available_judges(),
    }
