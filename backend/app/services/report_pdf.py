import io

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


class ReportPdfRenderer:
    def render(self, payload: dict) -> bytes:
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        y = height - 72

        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(72, y, "InterviewLoop Report")
        y -= 34
        pdf.setFont("Helvetica", 10)

        for key, value in payload.items():
            line = f"{key}: {value}"
            pdf.drawString(72, y, line[:110])
            y -= 18
            if y < 72:
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y = height - 72

        pdf.save()
        return buffer.getvalue()
