import re
from datetime import datetime
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt
try:
    import fitz  # PyMuPDF for redaction
except ModuleNotFoundError:
    print("请安装 PyMuPDF 库：pip install PyMuPDF")
    sys.exit(1)

def extract_codes(pdf_path):
    blocks = []
    pairs = []
    css_list = []
    quantity_list = []
    weight_list = []
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        # Find all matches for CSS# IATA MAWB Quantity Weight
        matches = list(re.finditer(r'\b(\w+)\s+(\d{3})\s+(\d{8})\s+(\d+)\s+([\d.]+)\b', text))
        for i, match in enumerate(matches):
            start = match.start()
            # Find the end as the position of "Total" after start
            text_after = text[start:]
            total_match = re.search(r'\bTotal\b', text_after)
            if total_match:
                end = start + total_match.end()
            else:
                end = matches[i+1].start() if i+1 < len(matches) else len(text)
            block = text[start:end].strip()
            blocks.append(block)
            css = match.group(1)
            css_list.append(css)
            iata = match.group(2)
            mawb = match.group(3)
            quantity = match.group(4)
            weight = match.group(5)
            quantity_list.append(quantity)
            weight_list.append(weight)
            pairs.append(f"{iata}-{mawb}")

    return blocks, pairs, css_list, quantity_list, weight_list, doc

def redact_codes(doc, lines_to_redact, output_path):
    for page_num in range(len(doc)):
        page = doc[page_num]
        for line in lines_to_redact:
            # Search for the entire line as a whole
            text_instances = page.search_for(line)
            for inst in text_instances:
                # Add a redaction annotation (black rectangle)
                page.add_redact_annot(inst, fill=(0, 0, 0))  # Black fill
        # Apply redactions
        page.apply_redactions()
    doc.save(output_path)
    doc.close()

class PDFRedactionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('PDF Redaction Tool')
        self.setGeometry(300, 300, 600, 200)

        layout = QVBoxLayout()

        # File selection
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel('选择PDF文件:'))
        self.file_entry = QLineEdit()
        file_layout.addWidget(self.file_entry)
        browse_button = QPushButton('浏览')
        browse_button.clicked.connect(self.select_file)
        file_layout.addWidget(browse_button)
        layout.addLayout(file_layout)

        # Codes input
        codes_layout = QHBoxLayout()
        codes_layout.addWidget(QLabel('输入提单号 (逗号分隔):'))
        self.codes_entry = QLineEdit()
        codes_layout.addWidget(self.codes_entry)
        layout.addLayout(codes_layout)

        # Generate button
        generate_button = QPushButton('生成')
        generate_button.clicked.connect(self.generate)
        layout.addWidget(generate_button)

        self.setLayout(layout)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, '选择PDF文件', '', 'PDF files (*.pdf)')
        if file_path:
            self.file_entry.setText(file_path)

    def generate(self):
        pdf_path = self.file_entry.text()
        if not pdf_path:
            QMessageBox.warning(self, '错误', '请选择PDF文件。')
            return
        codes_input = self.codes_entry.text()
        if not codes_input:
            QMessageBox.warning(self, '错误', '请输入提单号。')
            return
        specified_codes = [code.strip() for code in codes_input.split(',')]

        try:
            blocks, pairs, css_list, quantity_list, weight_list, doc = extract_codes(pdf_path)
            lines_to_redact = []
            for spec in specified_codes:
                if spec in pairs:
                    idx = pairs.index(spec)
                    lines_to_redact.append(blocks[idx])

            print("Blocks to redact:")
            for block in lines_to_redact:
                print(block)
                print("---")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f'{pdf_path[:-4]}_redacted_{timestamp}.pdf'
            redact_codes(doc, lines_to_redact, output_path)
            QMessageBox.information(self, '成功', f'涂黑PDF已保存为 {output_path}')
        except Exception as e:
            QMessageBox.critical(self, '错误', str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PDFRedactionApp()
    ex.show()
    sys.exit(app.exec_())
