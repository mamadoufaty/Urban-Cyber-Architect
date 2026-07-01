"""Validate Métropolis template produces full Club Urba cartography."""
from app.models.entities import Project
from app.services.project_templates import apply_template
from app.services.urbanism_schema import build_urbanism_schema
import uuid

payload = apply_template("metropolis", "Métropolis")
p = Project(
    id=uuid.uuid4(),
    name=payload["name"],
    organization=payload["organization"],
    objectives=payload["objectives"],
    urbanism=payload["urbanism"],
)
schema = build_urbanism_schema(p)
stats = schema["stats"]
by = stats["by_couche"]
print("objects:", stats["total_objects"])
print("relations:", stats["total_relations"])
print("by_couche:", by)
assert stats["total_objects"] >= 40, f"Expected 40+ objects, got {stats['total_objects']}"
assert stats["total_relations"] >= 80, f"Expected 80+ relations, got {stats['total_relations']}"
assert all(by.get(c, 0) > 0 for c in ("metier", "organisation", "fonctionnel", "applicatif", "technique"))
print("OK")
