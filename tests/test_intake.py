from pathlib import Path

from app.agents.intake_agent import IntakeAgent


def test_intake_generates_stable_id(tmp_path: Path):
    path = tmp_path / "a.pdf"
    path.write_bytes(b"demo")
    agent = IntakeAgent()
    assert agent.validate_and_register(path) == agent.validate_and_register(path)
