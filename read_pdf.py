import sys
import os
import PyPDF2

def dump_all_pdfs(pdf_folder, out_file):
    with open(out_file, 'w', encoding='utf-8') as fh:
        count = 0
        for fname in os.listdir(pdf_folder):
            if fname.endswith('.pdf'):
                pdf_path = os.path.join(pdf_folder, fname)
                count += 1
                fh.write(f"\n\n{'='*40}\n=== TÀI LIỆU {count}: {fname} ===\n{'='*40}\n")
                try:
                    with open(pdf_path, 'rb') as file:
                        reader = PyPDF2.PdfReader(file)
                        # Báo cáo VCP thường dài 15-20 trang, 6 trang đầu luôn là 15 Tiêu Chí (Đánh giá phẩm chất)
                        for i, page in enumerate(reader.pages[:6]):
                            fh.write(f"\n--- TRANG {i+1} ---\n")
                            text = page.extract_text()
                            if text: fh.write(text)
                except Exception as e:
                    fh.write(f"\nLỗi đọc file: {e}\n")
        print(f"Đã dump thành công {count} files thành TÀI LIỆU HUẤN LUYỆN tại {out_file}!")

if __name__ == "__main__":
    folder = r"C:\Users\thduy\OneDrive\05.DAU TU\02.CHUNG KHOAN\APP\AstraAI Signals\tai lieu tam soat co phieu"
    out = r"C:\Users\thduy\OneDrive\05.DAU TU\02.CHUNG KHOAN\APP\AstraAI Signals\astraai_signals\pdf_dump_utf8.txt"
    dump_all_pdfs(folder, out)
