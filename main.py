import os
import shutil
import fitz  # PyMuPDF

from textual.app import App, ComposeResult
from textual.widgets import (
    Input,
    Button,
    Static,
    RichLog,
    RadioSet,
    RadioButton,
)
from textual.containers import Vertical


SOURCE_DIR_NAME = "исходники PDF"
MERGED_FILENAME = "QR коды KASPI.pdf"
LAYOUT_4IN1_FILENAME = "QR коды KASPI (4 в 1).pdf"
LAYOUT_6IN1_FILENAME = "QR коды KASPI (6 в 1).pdf"


class PDFProcessor:
    def __init__(self, base_dir: str, log: RichLog):
        self.base_dir = base_dir
        self.source_dir = os.path.join(base_dir, SOURCE_DIR_NAME)
        self.log = log

    def process(self, layout_mode: str, with_border: bool):
        if not os.path.isdir(self.base_dir):
            self.log.write("❌ Неверный путь к папке")
            return

        self._create_source_dir()
        self._move_original_pdfs()
        self._crop_pdfs()
        self._merge_pdfs()
        
        if layout_mode == "4in1":
            self._create_4in1_layout(with_border)
        elif layout_mode == "6in1":
            self._create_6in1_layout(with_border)
        
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

    def _draw_border(self, page, rect, border_width=1, border_color=(0, 0, 0)):
        """Рисует рамку вокруг прямоугольника"""
        page.draw_rect(rect, color=border_color, width=border_width)

    def _create_4in1_layout(self, with_border=False):
        """Создает PDF с 4 обрезанными страницами на одной вертикальной странице (2x2)"""
        border_text = " с рамкой" if with_border else ""
        self.log.write(f"📐 Создание макета 4 в 1{border_text}...")
        
        # Открываем объединенный PDF
        source_pdf = fitz.open(os.path.join(self.base_dir, MERGED_FILENAME))
        output_pdf = fitz.open()
        
        total_pages = len(source_pdf)
        
        # Обрабатываем страницы группами по 4
        for i in range(0, total_pages, 4):
            # Получаем до 4 страниц
            pages_to_place = []
            for j in range(4):
                if i + j < total_pages:
                    pages_to_place.append(source_pdf[i + j])
                else:
                    pages_to_place.append(None)
            
            # Получаем размеры первой страницы
            first_page = pages_to_place[0]
            if first_page:
                page_width = first_page.rect.width
                page_height = first_page.rect.height
                
                # Создаем новую страницу A4 вертикальной ориентации (595 x 842)
                new_page = output_pdf.new_page(width=595, height=842)
                
                # Вычисляем позиции для размещения 2x2 (две сверху, две снизу)
                # Масштабируем страницы чтобы влезли
                scale = min(595 / 2 / page_width, 842 / 2 / page_height)
                
                scaled_width = page_width * scale
                scaled_height = page_height * scale
                
                # Позиции: (1-2 сверху, 3-4 снизу)
                positions = [
                    (0, 0),                              # Страница 1: верхний левый
                    (595 / 2, 0),                        # Страница 2: верхний правый
                    (0, 842 / 2),                        # Страница 3: нижний левый
                    (595 / 2, 842 / 2),                  # Страница 4: нижний правый
                ]
                
                # Размещаем страницы
                for idx, page in enumerate(pages_to_place):
                    if page:
                        x, y = positions[idx]
                        # Создаем прямоугольник для размещения
                        rect = fitz.Rect(x, y, x + scaled_width, y + scaled_height)
                        new_page.show_pdf_page(rect, source_pdf, page.number)
                        
                        # Рисуем рамку если нужно
                        if with_border:
                            self._draw_border(new_page, rect, border_width=1.5)
        
        # Сохраняем результат
        output_path = os.path.join(self.base_dir, LAYOUT_4IN1_FILENAME)
        output_pdf.save(output_path)
        output_pdf.close()
        source_pdf.close()
        
        self.log.write(f"📎 Создан макет 4 в 1{border_text}: {LAYOUT_4IN1_FILENAME}")

    def _create_6in1_layout(self, with_border=False):
        """Создает PDF с 6 обрезанными страницами на одной горизонтальной странице (2x3)"""
        border_text = " с рамкой" if with_border else ""
        self.log.write(f"📐 Создание макета 6 в 1{border_text}...")
        
        # Открываем объединенный PDF
        source_pdf = fitz.open(os.path.join(self.base_dir, MERGED_FILENAME))
        output_pdf = fitz.open()
        
        total_pages = len(source_pdf)
        
        # Обрабатываем страницы группами по 6
        for i in range(0, total_pages, 6):
            # Получаем до 6 страниц
            pages_to_place = []
            for j in range(6):
                if i + j < total_pages:
                    pages_to_place.append(source_pdf[i + j])
                else:
                    pages_to_place.append(None)
            
            # Получаем размеры первой страницы
            first_page = pages_to_place[0]
            if first_page:
                page_width = first_page.rect.width
                page_height = first_page.rect.height
                
                # Создаем новую страницу A4 горизонтальной ориентации (842 x 595)
                new_page = output_pdf.new_page(width=842, height=595)
                
                # Вычисляем позиции для размещения 2x3 (три сверху, три снизу)
                scale = min(842 / 3 / page_width, 595 / 2 / page_height)
                
                scaled_width = page_width * scale
                scaled_height = page_height * scale
                
                # Позиции: (1-2-3 сверху, 4-5-6 снизу)
                positions = [
                    (0, 0),                              # Страница 1: верхний левый
                    (842 / 3, 0),                        # Страница 2: верхний центр
                    (842 * 2 / 3, 0),                    # Страница 3: верхний правый
                    (0, 595 / 2),                        # Страница 4: нижний левый
                    (842 / 3, 595 / 2),                  # Страница 5: нижний центр
                    (842 * 2 / 3, 595 / 2),              # Страница 6: нижний правый
                ]
                
                # Размещаем страницы
                for idx, page in enumerate(pages_to_place):
                    if page:
                        x, y = positions[idx]
                        # Создаем прямоугольник для размещения
                        rect = fitz.Rect(x, y, x + scaled_width, y + scaled_height)
                        new_page.show_pdf_page(rect, source_pdf, page.number)
                        
                        # Рисуем рамку если нужно
                        if with_border:
                            self._draw_border(new_page, rect, border_width=1.5)
        
        # Сохраняем результат
        output_path = os.path.join(self.base_dir, LAYOUT_6IN1_FILENAME)
        output_pdf.save(output_path)
        output_pdf.close()
        source_pdf.close()
        
        self.log.write(f"📎 Создан макет 6 в 1{border_text}: {LAYOUT_6IN1_FILENAME}")

    def _cleanup_base_dir(self):
        for filename in os.listdir(self.base_dir):
            if (filename.lower().endswith(".pdf") and 
                filename not in [MERGED_FILENAME, LAYOUT_4IN1_FILENAME, LAYOUT_6IN1_FILENAME]):
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
    
    RadioSet {
        height: auto;
        padding: 0;
        margin: 0;
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
            
            yield Static("📐 Дополнительный макет")
            yield RadioSet(
                RadioButton("Только объединить", id="none", value=True),
                RadioButton("4 в 1 (вертикально 2×2)", id="four-in-one"),
                RadioButton("6 в 1 (горизонтально 2×3)", id="six-in-one"),
                id="layout_mode",
            )
            
            yield Static("🖼️ Рамка страницы")
            yield RadioSet(
                RadioButton("Без рамки", id="no-border", value=True),
                RadioButton("С рамкой", id="with-border"),
                id="border_mode",
            )
            
            yield Button("Обрезать и объединить PDF", id="process")

        yield RichLog(id="log", wrap=True)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id != "process":
            return

        # Определяем режим макета
        if self.query_one("#four-in-one", RadioButton).value:
            layout_mode = "4in1"
        elif self.query_one("#six-in-one", RadioButton).value:
            layout_mode = "6in1"
        else:
            layout_mode = "none"

        # Определяем режим рамки
        with_border = self.query_one("#with-border", RadioButton).value

        path = self.query_one("#dir", Input).value.strip()

        # Если путь вставлен в кавычках
        if (path.startswith("'") and path.endswith("'")) or \
        (path.startswith('"') and path.endswith('"')):
            path = path[1:-1]

        processor = PDFProcessor(
            path,
            self.query_one("#log", RichLog),
        )

        processor.process(layout_mode, with_border)


if __name__ == "__main__":
    PDFCutterApp().run()