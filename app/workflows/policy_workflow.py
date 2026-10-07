from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.clause_agent import ClauseAgent, ClauseExtraction
from app.agents.extraction_agent import ExtractionAgent
from app.agents.intake_agent import IntakeAgent
from app.agents.structuring_agent import StructuringAgent
from app.models.document import ExtractedDocument, TextChunk
from app.models.policy import PolicyData
from app.repositories.policy_repository import PolicyRepository
from app.services.chunking_service import ChunkingService


class WorkflowState(TypedDict, total=False):
    path: str
    document_id: str
    document: ExtractedDocument
    chunks: list[TextChunk]
    extraction: ClauseExtraction
    policy: PolicyData


class PolicyWorkflow:
    def __init__(self) -> None:
        self.intake = IntakeAgent()
        self.extraction = ExtractionAgent()
        self.chunking = ChunkingService()
        self.clause = ClauseAgent()
        self.structuring = StructuringAgent()
        self.repository = PolicyRepository()
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(WorkflowState)
        graph.add_node("intake", self._intake)
        graph.add_node("extract", self._extract)
        graph.add_node("chunk", self._chunk)
        graph.add_node("analyze", self._analyze)
        graph.add_node("structure", self._structure)
        graph.add_node("persist", self._persist)
        graph.add_edge(START, "intake")
        graph.add_edge("intake", "extract")
        graph.add_edge("extract", "chunk")
        graph.add_edge("chunk", "analyze")
        graph.add_edge("analyze", "structure")
        graph.add_edge("structure", "persist")
        graph.add_edge("persist", END)
        return graph.compile()

    def _intake(self, state: WorkflowState):
        document_id = self.intake.validate_and_register(Path(state["path"]))
        return {"document_id": document_id}

    def _extract(self, state: WorkflowState):
        document = self.extraction.run(Path(state["path"]), state["document_id"])
        return {"document": document}

    def _chunk(self, state: WorkflowState):
        return {"chunks": self.chunking.chunk_document(state["document"])}

    def _analyze(self, state: WorkflowState):
        return {"extraction": self.clause.run(state["chunks"])}

    def _structure(self, state: WorkflowState):
        document = state["document"]
        policy = self.structuring.run(state["document_id"], document.filename, state["extraction"])
        return {"policy": policy}

    def _persist(self, state: WorkflowState):
        self.repository.save_policy(state["policy"])
        return {}

    def run(self, path: str | Path) -> PolicyData:
        result = self.graph.invoke({"path": str(path)})
        return result["policy"]
