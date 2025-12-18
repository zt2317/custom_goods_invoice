import pdfplumber

with pdfplumber.open('AIR-0000419501 CES INVOICE.pdf') as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        print(text)
