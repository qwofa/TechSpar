import win32com.client
import os
import sys

docx_path = r"C:\Users\seigi\Desktop\26面试\简历.docx"
pdf_path = r"C:\Users\seigi\Desktop\26面试\简历.pdf"

if not os.path.exists(docx_path):
    print(f"文件不存在: {docx_path}")
    sys.exit(1)

print(f"正在打开: {docx_path}")

word = win32com.client.Dispatch("Word.Application")
word.Visible = False

try:
    doc = word.Documents.Open(os.path.abspath(docx_path))
    print("正在转换为 PDF...")
    doc.SaveAs(os.path.abspath(pdf_path), FileFormat=17)
    doc.Close()
    print(f"转换完成: {pdf_path}")
except Exception as e:
    print(f"转换失败: {e}")
finally:
    word.Quit()
