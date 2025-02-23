import os
import fitz  # PyMuPDF

def crop_pdfs(input_dir, output_dir, left, top, right, bottom):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pdf"):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            
            doc = fitz.open(input_path)
            for page in doc:
                rect = page.rect  # Исходный размер страницы
                new_rect = fitz.Rect(
                    rect.x0 + left,
                    rect.y0 + top,
                    rect.x1 - right,
                    rect.y1 - bottom
                )
                page.set_cropbox(new_rect)
            
            doc.save(output_path)
            doc.close()
            print(f"Обрезан и сохранён: {output_path}")

if __name__ == "__main__":
    input_directory = r"C:\Users\Astana\Desktop\Client"  # Папка с исходными PDF
    output_directory = r"C:\Users\Astana\Desktop\Client\pdf_обрезанные"  # Папка для сохранения
    
    crop_pdfs(input_directory, output_directory, 0, 0, 290, 400)
