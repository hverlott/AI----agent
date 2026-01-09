import unittest
from unittest.mock import MagicMock, patch
import io

# Copied from admin_multi.py to verify logic without importing the whole streamlit app
def extract_content_from_upload(upload, filename):
    name_lower = (filename or "").lower()
    content = ""
    parse_note = ""
    if name_lower.endswith((".txt", ".md")):
        try:
            content = upload.getvalue().decode("utf-8", errors="ignore")
        except Exception:
            content = upload.getvalue().decode("latin-1", errors="ignore")
    elif name_lower.endswith(".pdf"):
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(upload)
            pages = []
            for i in range(len(reader.pages)):
                text = reader.pages[i].extract_text()
                if text:
                    pages.append(f"# PDF Page {i+1}\n{text}")
            content = "\n\n".join(pages).strip()
            parse_note = "parsed:pdf"
        except Exception as e:
            parse_note = f"unparsed:pdf:{e}"
            content = ""
    # ... (other formats omitted for this test)
    else:
         # Simplified fallback
        try:
            content = upload.getvalue().decode("utf-8", errors="ignore")
        except Exception:
            content = ""
        parse_note = "unknown_format"
    return content, parse_note

class TestPDFParsing(unittest.TestCase):
    
    @patch('PyPDF2.PdfReader')
    def test_pdf_extract_chinese(self, mock_pdf_reader):
        # Mock the PDF content
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "这是一个测试页面。\n包含中文内容。"
        
        mock_reader_instance = MagicMock()
        mock_reader_instance.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader_instance
        
        # Mock the upload file object
        mock_upload = io.BytesIO(b"fake pdf content")
        
        content, note = extract_content_from_upload(mock_upload, "test.pdf")
        
        self.assertEqual(note, "parsed:pdf")
        self.assertIn("# PDF Page 1", content)
        self.assertIn("这是一个测试页面", content)
        self.assertIn("包含中文内容", content)

    @patch('PyPDF2.PdfReader')
    def test_pdf_extract_empty(self, mock_pdf_reader):
        # Mock empty PDF
        mock_reader_instance = MagicMock()
        mock_reader_instance.pages = []
        mock_pdf_reader.return_value = mock_reader_instance
        
        mock_upload = io.BytesIO(b"empty pdf")
        
        content, note = extract_content_from_upload(mock_upload, "empty.pdf")
        
        self.assertEqual(note, "parsed:pdf")
        self.assertEqual(content, "")

    def test_pdf_import_error(self):
        # Test when PyPDF2 raises an exception
        with patch('PyPDF2.PdfReader', side_effect=Exception("Corrupt PDF")):
            mock_upload = io.BytesIO(b"corrupt pdf")
            content, note = extract_content_from_upload(mock_upload, "corrupt.pdf")
            
            self.assertTrue(note.startswith("unparsed:pdf:Corrupt PDF"))
            self.assertEqual(content, "")

if __name__ == '__main__':
    unittest.main()
