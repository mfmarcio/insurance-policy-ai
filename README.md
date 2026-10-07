# PolicyCompare AI

MVP local para **leitura, extração, estruturação e comparação de apólices de seguro com IA Generativa**.

## Objetivo

Automatizar parte do trabalho de especialistas ao comparar apólices longas e juridicamente complexas, preservando rastreabilidade por página e evidência textual.

## Arquitetura

```text
PDF / imagem
    ↓
Intake Agent
    ↓
Extraction Agent (PyMuPDF / Tesseract)
    ↓
Chunking + recuperação TF-IDF
    ↓
Clause Agent (Ollama + JSON Schema)
    ↓
Structuring Agent (Pydantic)
    ↓
SQLite
    ↓
Comparison Agent (regras + LLM)
    ↓
Report Agent
    ↓
Streamlit + PDF comparativo
```

O workflow principal é orquestrado com **LangGraph**. Cada etapa possui responsabilidade explícita e pode ser substituída de forma independente.

## Agentes

1. **IntakeAgent** — valida formato, integridade básica e gera ID por hash SHA-256.
2. **ExtractionAgent** — extrai texto nativo do PDF e usa OCR para páginas sem camada textual; também lê imagens.
3. **ClauseAgent** — seleciona trechos relevantes e usa LLM local para identificar dados gerais, coberturas, exclusões e cláusulas especiais.
4. **StructuringAgent** — converte o retorno para modelo canônico Pydantic.
5. **QueryAgent** — responde perguntas sobre os dados estruturados da apólice, retornando evidências disponíveis.
6. **ComparisonAgent** — compara valores de forma determinística e usa similaridade textual/LLM para apoio semântico.
7. **ReportAgent** — cria relatório comparativo em PDF.

## Tecnologias

- Python 3.11+
- Streamlit
- Ollama (LLM local)
- Modelo sugerido: `qwen3:4b` (configurável)
- PyMuPDF
- Tesseract OCR
- Pydantic
- LangGraph
- SQLite
- scikit-learn / TF-IDF
- ReportLab

## Instalação rápida no Windows

### 1. Python

Instale Python 3.11 ou 3.12 e confirme:

```powershell
python --version
```

### 2. Ambiente virtual

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Ollama

Instale o Ollama e carregue um modelo local:

```powershell
ollama pull qwen3:4b
ollama run qwen3:4b
```

O serviço normalmente responde em `http://localhost:11434`.

### 4. Tesseract OCR

Instale o Tesseract OCR para Windows e o pacote de idioma português (`por`). Garanta que `tesseract.exe` esteja no `PATH`.

> PDFs com texto nativo não dependem de OCR; o Tesseract é usado para imagens e páginas digitalizadas.

### 5. Configuração

```powershell
copy .env.example .env
```

Ajuste o modelo no `.env` se desejar:

```env
OLLAMA_MODEL=qwen3:4b
```

### 6. Execução

```powershell
python run.py
```

ou:

```powershell
streamlit run frontend/streamlit_app.py
```

Abra `http://localhost:8501`.

## Demonstração

Na barra lateral da interface, clique em **Criar PDFs de demonstração**. Serão geradas duas apólices sintéticas em `samples/`.

1. Faça upload das duas apólices.
2. Clique em **Processar documentos**.
3. Use a aba **Consultar** para fazer perguntas sobre uma apólice estruturada.
4. Abra a aba **Comparar**.
5. Selecione A e B.
6. Execute a comparação.
7. Consulte diferenças, páginas/evidências e gere o PDF comparativo.

## Estrutura dos dados

Cada cobertura pode manter:

```json
{
  "name": "Incêndio",
  "limit_value": 1000000,
  "currency": "BRL",
  "deductible_value": 10000,
  "evidence": {
    "page": 15,
    "text": "Limite máximo de indenização...",
    "confidence": 0.96
  }
}
```

Essa evidência permite ao usuário revisar a origem da conclusão da IA.

## Estratégia de comparação

O projeto usa abordagem híbrida:

- **Código determinístico** para valores, limites, franquias e existência de itens.
- **Similaridade textual** para parear cláusulas com nomenclaturas próximas.
- **LLM** para extração semântica e resumo executivo.

Classificações:

- `EQUIVALENTE`
- `MAIS_FAVORAVEL_A`
- `MAIS_FAVORAVEL_B`
- `SOMENTE_A`
- `SOMENTE_B`
- `DIFERENTE`
- `INCONCLUSIVO`

## Segurança e credenciais

A solução padrão não depende de chaves de API externas. O Ollama roda localmente. Configurações ficam em `.env`, que está ignorado pelo Git.

## Tratamento de erros

- validação de formato e arquivo vazio;
- timeout e mensagens para indisponibilidade do Ollama;
- validação de resposta do LLM via JSON Schema/Pydantic;
- fallback de OCR em páginas com pouco texto;
- persistência isolada em repositório SQLite;
- comparação com fallback determinístico caso o resumo generativo falhe.

## Limitações conhecidas

- O MVP não substitui análise jurídica ou técnica de seguros.
- O desempenho depende do modelo local e do hardware.
- Tabelas complexas e PDFs com layout muito irregular podem exigir extração especializada.
- O recuperador TF-IDF é leve e local, mas pode ser substituído por embeddings + Qdrant/Chroma em uma evolução.
- A ontologia de coberturas/exclusões ainda é genérica; em produção deve ser especializada por ramo de seguro.
- Não há autenticação, RBAC ou criptografia de documentos neste MVP.

## Evoluções sugeridas

1. Embeddings multilíngues + Qdrant/pgvector.
2. OCR de layout/document intelligence para tabelas.
3. Human-in-the-loop para baixa confiança.
4. Ontologias por ramo (Auto, D&O, Cyber, Patrimonial etc.).
5. Extração paralela por seção/página.
6. Avaliação automática com dataset rotulado (precision/recall por campo).
7. Versionamento de prompts e observabilidade LLM.
8. API FastAPI para integração externa.
9. Autenticação, trilha de auditoria e criptografia.
10. Exportação Excel/JSON e relatório executivo mais sofisticado.

## Testes

```powershell
pytest -q
```

## Aviso

Projeto de demonstração. As respostas geradas por IA devem ser verificadas por profissional qualificado antes de decisões de cobertura, contratação ou interpretação jurídica.
