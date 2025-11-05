import fitz  # PyMuPDF
import requests
from pathlib import Path

class PDFProcessor:
    def __init__(self, cache_dir: str = "cache/pdfs"):
        """Initialize PDF processor"""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_text(self, pdf_url: str) -> str:
        """Download and extract text from PDF"""
        # Download PDF
        pdf_path = self._download_pdf(pdf_url)
        
        if not pdf_path:
            return ""
        
        # Extract text
        doc = fitz.open(pdf_path)
        text = ""
        
        for page in doc:
            text += page.get_text()
        
        doc.close()
        return text
    
    def _download_pdf(self, url: str) -> Path:
        """Download PDF to cache"""
        filename = url.split('/')[-1]
        if not filename.endswith('.pdf'):
            filename += '.pdf'
        
        pdf_path = self.cache_dir / filename
        
        if pdf_path.exists():
            return pdf_path
        
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(pdf_path, 'wb') as f:
                    f.write(response.content)
                return pdf_path
        except:
            return None