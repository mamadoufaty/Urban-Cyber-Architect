"""Relations acteur → procédure / opération (R15, R31)."""

from app.metamodel.urbanism import (
    REFERENCE_RELATIONS,
    RULE_BY_ID,
    validate_metamodel_implementation,
    validate_relation,
)


def test_acteur_realise_operation_exists():
    assert validate_relation("acteur", "réalise", "operation")
    assert RULE_BY_ID["R15"]["type"] == "réalise"
    assert RULE_BY_ID["R15"]["target"] == "operation"


def test_acteur_pilote_procedure():
    assert validate_relation("acteur", "pilote", "procedure")
    rule = RULE_BY_ID["R31"]
    assert rule["source"] == "acteur"
    assert rule["type"] == "pilote"
    assert rule["target"] == "procedure"
    assert rule["category"] == "organisation"


def test_metamodel_validation_includes_r31():
    report = validate_metamodel_implementation()
    assert report["status"] == "ok"
    assert len(REFERENCE_RELATIONS) == 31
    assert "R31" in RULE_BY_ID
