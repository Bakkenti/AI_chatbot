import io
from openpyxl import Workbook
from datetime import datetime
from ...db import models as db

async def handle_extract(table_name: str):
    table_name = table_name.strip()
    if not await db.test_db_connection():
        empty_bytes = io.BytesIO()
        wb = Workbook()
        wb.save(empty_bytes)
        empty_bytes.seek(0)
        return empty_bytes.getvalue(), f"{table_name}.xlsx"

    columns, rows = await db.fetch_table_preview(table_name)
    wb = Workbook()
    ws = wb.active
    ws.append(columns)

    for row in rows:
        cleaned_row = []
        for col in columns:
            val = row.get(col, "")
            if isinstance(val, datetime):
                if val.tzinfo:
                    val = val.replace(tzinfo=None)
            cleaned_row.append(val)
        ws.append(cleaned_row)

    excel_bytes = io.BytesIO()
    wb.save(excel_bytes)
    excel_bytes.seek(0)
    base_filename = f"{table_name}.xlsx"
    return excel_bytes.getvalue(), base_filename


async def handle_find(message: str) -> str:
    try:
        _, keyword = message.split(maxsplit=1)
        results = await db.search_keyword_global(keyword)
        if not results:
            return f"No documents found for '{keyword}'."

        output = ""
        for table_name, rows in results:
            if not rows:
                continue
            output += f"{table_name.strip()}:\n"
            for row in rows:
                row_display = ", ".join(f"{k}: {v}" for k, v in row.items())
                output += f"- {row_display}\n"
            output += "\n"
        return output.strip()
    except Exception as e:
        return f"Error while searching: {e}"