from .commands.text import handle_time, handle_help, handle_sum
from .commands.pdf import handle_pdf, handle_savepdf_to_storage, handle_extract_to_storage
from .commands.db_ops import handle_extract, handle_find
from .ai import ask_ai

class LastAIMessageStore:
    def __init__(self):
        self.messages = {}

    def set_message(self, chat_id: int, message: str):
        self.messages[chat_id] = message

    def get_message(self, chat_id: int) -> str:
        return self.messages.get(chat_id, "")

last_ai_message_store = LastAIMessageStore()

def handle_command(message: str):
    if message.startswith("/time"):
        return handle_time()
    if message.startswith("/help"):
        return handle_help()
    if message.startswith("/sum"):
        return handle_sum(message)
    return None

async def dispatch(message: str, chat_id: int = None, local_only: bool = False):
    command_result = handle_command(message)
    if command_result:
        return command_result

    if message.startswith("/find"):
        return await handle_find(message)

    if message.startswith("savestorage"):
        try:
            _, filename = message.split(" ", 1)
            filename = filename.strip()
            if not chat_id:
                return "Chat ID not provided"
            text_to_save = last_ai_message_store.get_message(chat_id)
            if not text_to_save:
                return "No AI message to save"
            result = await handle_savepdf_to_storage(text_to_save, filename)
            return f"Saved to MinIO: {result}"
        except ValueError:
            return "Usage: savestorage <filename>"
        except Exception as e:
            return f"Error: {e}"

    if message.startswith("/extract"):
        try:
            parts = message.strip().split(maxsplit=1)
            if len(parts) != 2:
                return "Usage: /extract table_name"

            table_name = parts[1].strip()
            excel_bytes, base_filename = await handle_extract(table_name)
            saved_name = await handle_extract_to_storage(table_name, base_filename, excel_bytes)
            return f"Extracted to MinIO: {saved_name}"
        except Exception as e:
            return f"Error during extraction: {e}"

    if message.startswith("/readpdf"):
        return "Please upload a PDF file to read"

    if local_only:
        return f"Command not recognized locally: {message}"

    try:
        response = await ask_ai(message)
        if chat_id:
            last_ai_message_store.set_message(chat_id, response)
        return response
    except Exception as e:
        return f"AI Error: {e}"
