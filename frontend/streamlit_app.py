from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agents.comparison_agent import ComparisonAgent
from app.agents.report_agent import ReportAgent
from app.agents.query_agent import QueryAgent
from app.config.settings import get_settings
from app.repositories.policy_repository import PolicyRepository
from app.services.demo_service import create_demo_pdfs
from app.services.llm_service import LLMService
from app.workflows.policy_workflow import PolicyWorkflow


st.set_page_config(page_title="PolicyCompare AI", page_icon="📄", layout="wide")
settings = get_settings()
repo = PolicyRepository()
llm = LLMService()

st.title("PolicyCompare AI")
st.caption("MVP local para extração, estruturação e comparação inteligente de apólices de seguro")

with st.sidebar:
    st.subheader("Ambiente")
    st.write(f"Modelo: `{settings.ollama_model}`")
    available = llm.is_available()
    st.success("Ollama disponível") if available else st.warning("Ollama não encontrado")
    st.caption("A análise generativa requer Ollama em execução. O restante da interface pode ser explorado normalmente.")

    if st.button("Criar PDFs de demonstração"):
        a, b = create_demo_pdfs(ROOT / "samples")
        st.success(f"Criados: {a.name} e {b.name}")


tab_upload, tab_policies, tab_query, tab_compare, tab_arch = st.tabs(["1. Processar", "2. Apólices", "3. Consultar", "4. Comparar", "Arquitetura"])

with tab_upload:
    st.subheader("Recebimento e processamento")
    uploads = st.file_uploader(
        "Envie uma ou mais apólices",
        type=["pdf", "png", "jpg", "jpeg", "tif", "tiff"],
        accept_multiple_files=True,
    )
    if uploads and st.button("Processar documentos", type="primary"):
        if not available:
            st.error("O Ollama não está disponível. Inicie o Ollama e carregue o modelo configurado antes de processar.")
        else:
            workflow = PolicyWorkflow()
            progress = st.progress(0)
            for idx, uploaded in enumerate(uploads, start=1):
                target = settings.upload_dir / uploaded.name
                target.write_bytes(uploaded.getvalue())
                with st.status(f"Processando {uploaded.name}", expanded=True) as status:
                    try:
                        policy = workflow.run(target)
                        st.write(f"Documento estruturado: {policy.policy_id}")
                        st.json(policy.model_dump(mode="json"), expanded=False)
                        status.update(label=f"{uploaded.name} concluído", state="complete")
                    except Exception as exc:
                        status.update(label=f"Falha em {uploaded.name}", state="error")
                        st.exception(exc)
                progress.progress(idx / len(uploads))

with tab_policies:
    st.subheader("Dados estruturados")
    policies = repo.list_policies()
    if not policies:
        st.info("Nenhuma apólice processada ainda.")
    for policy in policies:
        with st.expander(f"{policy.document_name} — {policy.insurer or 'Seguradora não identificada'}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Coberturas", len(policy.coverages))
            c2.metric("Exclusões", len(policy.exclusions))
            c3.metric("Cláusulas especiais", len(policy.special_clauses))
            st.json(policy.model_dump(mode="json"))

with tab_query:
    st.subheader("Consulta inteligente")
    policies = repo.list_policies()
    if not policies:
        st.info("Processe ao menos uma apólice para realizar consultas.")
    else:
        labels = {f"{p.document_name} ({p.policy_id})": p for p in policies}
        selected = st.selectbox("Apólice", list(labels), key="query_policy")
        question = st.text_input("Pergunta", placeholder="Ex.: Qual é a franquia da cobertura de danos elétricos?")
        if st.button("Consultar apólice") and question.strip():
            if not available:
                st.error("O Ollama não está disponível.")
            else:
                try:
                    answer = QueryAgent().run(labels[selected], question.strip())
                    st.markdown("### Resposta")
                    st.write(answer.answer)
                    if answer.inconclusive:
                        st.warning("A resposta foi classificada como inconclusiva com os dados estruturados disponíveis.")
                    if answer.evidence:
                        st.markdown("### Evidências")
                        for ev in answer.evidence:
                            st.markdown(f"**Página {ev.page or '-'} — confiança {ev.confidence:.2f}**")
                            st.write(ev.text)
                except Exception as exc:
                    st.exception(exc)

with tab_compare:
    st.subheader("Comparação A × B")
    policies = repo.list_policies()
    if len(policies) < 2:
        st.info("Processe pelo menos duas apólices para habilitar a comparação.")
    else:
        labels = {f"{p.document_name} ({p.policy_id})": p for p in policies}
        keys = list(labels)
        col1, col2 = st.columns(2)
        selected_a = col1.selectbox("Apólice A", keys, index=0)
        selected_b = col2.selectbox("Apólice B", keys, index=1 if len(keys) > 1 else 0)
        if st.button("Comparar apólices", type="primary"):
            if selected_a == selected_b:
                st.warning("Selecione apólices diferentes.")
            else:
                a, b = labels[selected_a], labels[selected_b]
                comparison = ComparisonAgent().run(a, b)
                repo.save_comparison(comparison)
                st.subheader("Resumo executivo")
                st.write(comparison.summary)
                df = pd.DataFrame([
                    {
                        "Dimensão": i.dimension,
                        "Item": i.item,
                        "Apólice A": i.policy_a,
                        "Apólice B": i.policy_b,
                        "Classificação": i.status,
                        "Página A": i.evidence_a.page if i.evidence_a else None,
                        "Página B": i.evidence_b.page if i.evidence_b else None,
                    }
                    for i in comparison.items
                ])
                st.dataframe(df, use_container_width=True, hide_index=True)

                st.subheader("Evidências")
                for item in comparison.items:
                    if item.evidence_a or item.evidence_b:
                        with st.expander(f"{item.dimension} — {item.item} — {item.status}"):
                            if item.evidence_a:
                                st.markdown(f"**A — página {item.evidence_a.page or '-'}**")
                                st.write(item.evidence_a.text)
                            if item.evidence_b:
                                st.markdown(f"**B — página {item.evidence_b.page or '-'}**")
                                st.write(item.evidence_b.text)

                pdf = ReportAgent().build_pdf(a, b, comparison)
                st.download_button(
                    "Baixar relatório comparativo em PDF",
                    data=pdf,
                    file_name="comparacao_apolices.pdf",
                    mime="application/pdf",
                )

with tab_arch:
    st.subheader("Fluxo multiagente")
    st.code(
        """
Upload PDF/Imagem
      │
      ▼
Intake Agent ── validação/hash
      │
      ▼
Extraction Agent ── PyMuPDF + OCR fallback
      │
      ▼
Chunking + Retrieval local
      │
      ▼
Clause Agent ── Ollama + saída JSON estruturada
      │
      ▼
Structuring Agent ── Pydantic
      │
      ▼
SQLite
      │
      ├──────────────► Consulta / evidências
      ▼
Comparison Agent ── regras + IA generativa
      │
      ▼
Report Agent ── PDF comparativo
        """,
        language="text",
    )
    st.markdown("**Princípio:** IA interpreta; código valida e compara determinísticamente sempre que possível.")
