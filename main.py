import os
import shutil
import fitz  # PyMuPDF

from textual.app import App, ComposeResult
from textual.widgets import (
    Input,
    Button,
    Static,
    RichLog,
)
from textual.containers import Vertical


SOURCE_DIR_NAME = "исходники PDF"
MERGED_FILENAME = "QR коды KASPI.pdf"


class PDFProcessor:
    def __init__(self, base_dir: str, log: RichLog):
        self.base_dir = base_dir
        self.source_dir = os.path.join(base_dir, SOURCE_DIR_NAME)
        self.log = log

    def process(self):
        if not os.path.isdir(self.base_dir):
            self.log.write("❌ Неверный путь к папке")
            return

        self._create_source_dir()
        self._move_original_pdfs()
        self._crop_pdfs()
        self._merge_pdfs()
        self._cleanup_base_dir()

        self.log.write("✅ Готово")

    def _create_source_dir(self):
        os.makedirs(self.source_dir, exist_ok=True)
        self.log.write(f"📁 Папка создана: {SOURCE_DIR_NAME}")

    def _move_original_pdfs(self):
        for filename in os.listdir(self.base_dir):
            if filename.lower().endswith(".pdf"):
                shutil.move(
                    os.path.join(self.base_dir, filename),
                    os.path.join(self.source_dir, filename),
                )
                self.log.write(f"📦 Перемещён: {filename}")

    def _crop_pdfs(self):
        left = 0
        top = 400
        right = 290
        bottom = 0

        for filename in os.listdir(self.source_dir):
            if not filename.lower().endswith(".pdf"):
                continue

            src = os.path.join(self.source_dir, filename)
            dst = os.path.join(self.base_dir, filename)

            doc = fitz.open(src)

            for page in doc:
                rect = page.rect

                new_rect = fitz.Rect(
                    rect.x0 + left,
                    rect.y0 + top,
                    rect.x1 - right,
                    rect.y1 - bottom,
                )

                page.set_cropbox(new_rect)
                page.set_mediabox(new_rect)

            doc.save(dst)
            doc.close()
            self.log.write(f"✂️ Обрезан: {filename}")

    def _merge_pdfs(self):
        merged = fitz.open()
        output_path = os.path.join(self.base_dir, MERGED_FILENAME)

        for filename in sorted(os.listdir(self.base_dir)):
            if filename.lower().endswith(".pdf") and filename != MERGED_FILENAME:
                with fitz.open(os.path.join(self.base_dir, filename)) as pdf:
                    merged.insert_pdf(pdf)
                    self.log.write(f"📄 Добавлен: {filename}")

        merged.save(output_path)
        merged.close()
        self.log.write(f"📎 Итоговый файл: {MERGED_FILENAME}")

    def _cleanup_base_dir(self):
        for filename in os.listdir(self.base_dir):
            if filename.lower().endswith(".pdf") and filename != MERGED_FILENAME:
                os.remove(os.path.join(self.base_dir, filename))
                self.log.write(f"🗑️ Удалён: {filename}")


class PDFCutterApp(App):

    CSS = """
    Screen {
        layout: vertical;
    }
    
    #controls {
        height: auto;
        padding: 0 1;
    }
    
    RichLog {
        height: 1fr;
        border: solid gray;
        margin-top: 1;
    }
    
    Input {
        margin: 0;
    }
    
    Static {
        height: 1;
        padding: 0;
    }
    
    Button {
        margin-top: 1;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="controls"):
            yield Static("📂 Путь к папке с PDF")
            yield Input(placeholder="C:/PDF", id="dir")
            yield Button("Обрезать и объединить PDF", id="process")

        yield RichLog(id="log", wrap=True)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id != "process":
            return

        processor = PDFProcessor(
            self.query_one("#dir", Input).value,
            self.query_one("#log", RichLog),
        )

        processor.process()


if __name__ == "__main__":
    PDFCutterApp().run()