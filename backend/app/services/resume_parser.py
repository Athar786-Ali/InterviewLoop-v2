import io
import logging
import re

from app.core.exceptions import AppError

logger = logging.getLogger(__name__)

# 2 MB upload ceiling — large enough for any realistic resume PDF
MAX_RESUME_BYTES = 2 * 1024 * 1024


class ResumeParserService:
    """Extracts plain text from a resume supplied as either PDF bytes or raw text.

    Uses `pypdf` for PDF parsing — pure Python, no C extension required.
    No external API calls; fully offline.
    """

    def parse_pdf(self, file_bytes: bytes) -> str:
        """Extract text from a PDF resume.

        Args:
            file_bytes: Raw bytes of the uploaded PDF file.

        Returns:
            Cleaned extracted text suitable for LLM context injection.

        Raises:
            AppError: If the file is too large, not a valid PDF, or yields no text.
        """
        if len(file_bytes) > MAX_RESUME_BYTES:
            raise AppError(
                "RESUME_TOO_LARGE",
                f"Resume file must be under {MAX_RESUME_BYTES // 1024 // 1024} MB.",
                413,
            )

        try:
            from pypdf import PdfReader  # lazy import — only loaded when needed

            reader = PdfReader(io.BytesIO(file_bytes))
        except Exception as exc:
            logger.warning("resume_pdf_parse_failed", extra={"error": str(exc)})
            raise AppError("RESUME_PARSE_FAILED", "Could not parse the uploaded PDF. Ensure it is a valid PDF file.", 422) from exc

        pages: list[str] = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pages.append(text)

        raw_text = "\n".join(pages)
        cleaned = self._clean(raw_text)

        if not cleaned:
            raise AppError(
                "RESUME_EMPTY",
                "No readable text was found in the PDF. Try uploading a text-based (not scanned/image) PDF.",
                422,
            )

        logger.info("resume_pdf_parsed", extra={"page_count": len(reader.pages), "char_count": len(cleaned)})
        return cleaned

    def parse_text(self, raw_text: str) -> str:
        """Normalise and clean a plain-text resume string.

        Args:
            raw_text: Raw text pasted or uploaded by the user.

        Returns:
            Cleaned text suitable for LLM context injection.

        Raises:
            AppError: If the text is empty after cleaning.
        """
        cleaned = self._clean(raw_text)
        if not cleaned:
            raise AppError("RESUME_EMPTY", "Resume text is empty after cleaning. Please provide resume content.", 422)
        return cleaned

    @staticmethod
    def _clean(text: str) -> str:
        """Remove excessive whitespace and non-printable characters."""
        # Collapse runs of spaces / tabs to a single space
        text = re.sub(r"[ \t]+", " ", text)
        # Collapse more than 2 consecutive newlines to 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
