from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.policy import PolicyComparison, PolicyData


class ReportAgent:
    def build_pdf(self, a: PolicyData, b: PolicyData, comparison: PolicyComparison) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5 * cm, leftMargin=1.5 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
        styles = getSampleStyleSheet()
        story = [
            Paragraph("Relatório Comparativo de Apólices", styles["Title"]),
            Spacer(1, 10),
            Paragraph(f"Apólice A: {a.document_name}", styles["Normal"]),
            Paragraph(f"Apólice B: {b.document_name}", styles["Normal"]),
            Spacer(1, 10),
            Paragraph("Resumo executivo", styles["Heading2"]),
            Paragraph(comparison.summary or "Sem resumo disponível.", styles["BodyText"]),
            Spacer(1, 12),
            Paragraph("Diferenças identificadas", styles["Heading2"]),
        ]
        data = [["Dimensão", "Item", "A", "B", "Status"]]
        for item in comparison.items:
            data.append([
                item.dimension,
                item.item,
                (item.policy_a or "-")[:250],
                (item.policy_b or "-")[:250],
                item.status,
            ])
        table = Table(data, colWidths=[2.3 * cm, 3.4 * cm, 5.0 * cm, 5.0 * cm, 2.8 * cm], repeatRows=1)
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.25, None),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ]))
        story.append(table)
        story.append(Spacer(1, 10))
        story.append(Paragraph("Observação: resultado gerado por IA para apoio à análise. Deve ser validado por especialista antes de qualquer decisão contratual ou jurídica.", styles["Italic"]))
        doc.build(story)
        return buffer.getvalue()
