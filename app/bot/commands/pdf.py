import os
import uuid
from fpdf import FPDF
from ...storage import minio_client as storage
import io
import base64
import PyPDF2
import asyncio

async def handle_savepdf_to_storage(text: str, filename: str) -> str:
    pdf = FPDF()
    pdf.add_page()

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    font_path = os.path.join(project_root, "static", "fonts", "DejaVuSans.ttf")

    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Font file not found at {font_path}")

    pdf.add_font("DejaVu", "", font_path, uni=True)
    pdf.set_font("DejaVu", size=12)

    for line in text.split("\n"):
        pdf.multi_cell(0, 8, line)

    pdf_bytes = pdf.output(dest="S").encode("latin-1", "replace")

    storage.client.put_object(
        bucket_name=storage.BUCKET_NAME,
        object_name=filename,
        data=io.BytesIO(pdf_bytes),
        length=len(pdf_bytes),
        content_type="application/pdf"
    )

    return filename


async def handle_extract_to_storage(table_name: str, filename: str, excel_bytes: bytes) -> str:
    try:
        if storage.client.bucket_exists(storage.BUCKET_NAME):
            exists = any(obj.object_name == filename for obj in storage.client.list_objects(storage.BUCKET_NAME))
            if exists:
                base, ext = os.path.splitext(filename)
                filename = f"{base}_{uuid.uuid4().hex[:12]}{ext}"

        storage.client.put_object(
            bucket_name=storage.BUCKET_NAME,
            object_name=filename,
            data=io.BytesIO(excel_bytes),
            length=len(excel_bytes),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        print(f"Uploaded to MinIO: {filename}")
        return filename

    except Exception as e:
        print(f"Error uploading Excel: {e}")
        return None


def handle_pdf(pdf_bytes: bytes, filename: str = None) -> str:
    try:
        pdf = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = "".join([page.extract_text() or "" for page in pdf.pages])
        return text.strip() or "No text found."
    except Exception as e:
        return f"Error while processing PDF: {e}"



def handle_savepdf(text: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.split("\n"):
        pdf.multi_cell(0, 8, line)
    return pdf.output(dest="S").encode("latin1")


async def handle_delete_from_storage(filename: str):
    try:
        if storage.client.bucket_exists(storage.BUCKET_NAME):
            storage.client.remove_object(storage.BUCKET_NAME, filename)
            return True
    except Exception as e:
        print(f"Error deleting {filename}: {e}")
    return False