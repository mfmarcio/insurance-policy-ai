from pathlib import Path

import fitz


SAMPLE_A = """APÓLICE EMPRESARIAL DEMO A
Seguradora: Seguradora Horizonte S.A.
Número da Apólice: DEMO-A-001
Segurado: Empresa Exemplo Ltda.
Produto: Seguro Empresarial
Vigência: 01/01/2026 a 31/12/2026

COBERTURAS
1. Incêndio, raio e explosão. Limite Máximo de Indenização: R$ 1.000.000,00. Franquia: R$ 10.000,00.
2. Danos elétricos. Limite Máximo de Indenização: R$ 200.000,00. Franquia: R$ 5.000,00.
3. Roubo de bens. Limite Máximo de Indenização: R$ 150.000,00. Franquia: R$ 3.000,00.

RISCOS EXCLUÍDOS
Não estão cobertos danos decorrentes de guerra, atos de hostilidade, contaminação nuclear e dolo do segurado.

CLÁUSULA ESPECIAL
Para lucros cessantes, o período indenitário máximo é de 90 dias, condicionado à ocorrência de sinistro coberto por danos materiais.
"""

SAMPLE_B = """APÓLICE EMPRESARIAL DEMO B
Seguradora: Seguradora Atlântico S.A.
Número da Apólice: DEMO-B-001
Segurado: Empresa Exemplo Ltda.
Produto: Seguro Patrimonial Empresarial
Vigência: 01/01/2026 a 31/12/2026

COBERTURAS
1. Incêndio, queda de raio e explosão. Limite Máximo de Indenização: R$ 800.000,00. Franquia: R$ 15.000,00.
2. Roubo e furto qualificado. Limite Máximo de Indenização: R$ 200.000,00. Franquia: R$ 4.000,00.
3. Alagamento. Limite Máximo de Indenização: R$ 100.000,00. Franquia: R$ 10.000,00.

RISCOS EXCLUÍDOS
Excluem-se prejuízos causados por guerra, invasão, rebelião, radiação nuclear, dolo e atos ilícitos intencionais do segurado.

CLÁUSULA ESPECIAL
A cobertura de lucros cessantes prevê período indenitário máximo de 180 dias, desde que decorrente de dano material amparado pela apólice.
"""


def create_demo_pdfs(output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for name, content in [("apolice_demo_A.pdf", SAMPLE_A), ("apolice_demo_B.pdf", SAMPLE_B)]:
        path = output_dir / name
        doc = fitz.open()
        page = doc.new_page()
        rect = fitz.Rect(50, 50, 545, 792)
        page.insert_textbox(rect, content, fontsize=11, fontname="helv", lineheight=1.35)
        doc.save(path)
        files.append(path)
    return files[0], files[1]
