from app.agents.comparison_agent import ComparisonAgent
from app.models.policy import Coverage, Evidence, PolicyData


def test_higher_limit_favors_a():
    a = PolicyData(
        policy_id="a",
        document_name="a.pdf",
        coverages=[Coverage(name="Incêndio", limit_value=1000000, currency="BRL", evidence=Evidence(page=1, text="x", confidence=1))],
    )
    b = PolicyData(
        policy_id="b",
        document_name="b.pdf",
        coverages=[Coverage(name="Incêndio", limit_value=800000, currency="BRL", evidence=Evidence(page=1, text="x", confidence=1))],
    )
    result = ComparisonAgent().run(a, b)
    item = next(x for x in result.items if x.dimension == "Cobertura")
    assert item.status == "MAIS_FAVORAVEL_A"
