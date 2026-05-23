import sys
print("Python version:", sys.version)
for m in ['fpdf', 'reportlab', 'pdfkit', 'pypdf', 'pypdf2', 'PyPDF2']:
    try:
        __import__(m)
        print(m, "available")
    except ImportError:
        print(m, "NOT available")
