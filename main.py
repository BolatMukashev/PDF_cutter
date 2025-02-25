import os
import fitz  # PyMuPDF

class PDFCutter:
    input_dir = r"C:\Users\Astana\Desktop\Client"
    output_dir = r"C:\Users\Astana\Desktop\Client\pdf_обрезанные"

    def crop_pdfs(self, left=0, top=400, right=290, bottom=0):
        """Обрезает PDF, изменяя область видимости страниц (CropBox)."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        for filename in os.listdir(self.input_dir):
            if filename.lower().endswith(".pdf"):
                input_path = os.path.join(self.input_dir, filename)
                output_path = os.path.join(self.output_dir, filename)

                doc = fitz.open(input_path)

                for page in doc:
                    rect = page.rect  # Исходный размер страницы
                    new_rect = fitz.Rect(
                        rect.x0 + left,
                        rect.y0 + top,
                        rect.x1 - right,
                        rect.y1 - bottom
                    )
                    page.set_cropbox(new_rect)  # Устанавливаем обрезку
                    page.set_mediabox(new_rect)  # Реально изменяем размеры страницы
                
                doc.save(output_path)
                doc.close()
                print(f"✅ Обрезан и сохранён: {output_path}")

    def merge_pdfs(self):
        """Объединяет все PDF в один."""
        output_file = os.path.join(self.output_dir, "QR коды KASPI.pdf")
        pdf_merger = fitz.open()
        
        for filename in sorted(os.listdir(self.output_dir)):  # Сортируем для порядка
            if filename.lower().endswith(".pdf"):
                file_path = os.path.join(self.output_dir, filename)
                with fitz.open(file_path) as pdf_doc:  # Открываем PDF внутри `with`
                    pdf_merger.insert_pdf(pdf_doc)  # Вставляем PDF
                    print(f"📄 Добавлен: {file_path}")
        
        pdf_merger.save(output_file)
        pdf_merger.close()
        print(f"✅ Объединённый файл сохранён: {output_file}")

    def delete_non_qr_pdfs(self):
        """Удаляет все PDF, которые не начинаются с 'QR'."""
        for filename in os.listdir(self.output_dir):
            if filename.lower().endswith(".pdf") and not filename.startswith("QR"):
                file_path = os.path.join(self.output_dir, filename)
                os.remove(file_path)
                print(f"🗑️ Удалён: {file_path}")

if __name__ == "__main__":
    new_pdf_cutter = PDFCutter()
    new_pdf_cutter.crop_pdfs()
    new_pdf_cutter.merge_pdfs()
    new_pdf_cutter.delete_non_qr_pdfs()
