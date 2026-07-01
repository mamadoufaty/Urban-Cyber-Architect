"""Blank project must have zero Club Urba objects."""
from app.models.entities import Project
from app.services.project_templates import apply_template
from app.services.urbanism_schema import build_urbanism_schema
import uuid

payload = apply_template("blank", "Mon projet vierge")
p = Project(
    id=uuid.uuid4(),
    name=payload["name"],
    organization=payload["organization"],
    objectives=payload["objectives"],
    urbanism=payload["urbanism"],
)
schema = build_urbanism_schema(p)
assert schema["stats"]["total_objects"] == 0, schema["stats"]
assert schema["stats"]["total_relations"] == 0
print("blank OK:", schema["stats"])

payload2 = apply_template("metropolis", "Métropolis")
p2 = Project(
    id=uuid.uuid4(),
    name=payload2["name"],
    organization=payload2["organization"],
    objectives=payload2["objectives"],
    urbanism=payload2["urbanism"],
)
schema2 = build_urbanism_schema(p2)
assert schema2["stats"]["total_objects"] >= 40
print("example OK:", schema2["stats"])
