import sys
import json
from pathlib import Path
from PyPDF2 import PdfReader
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def dump_pdf_metadata(pdf_path: str) -> dict:
    """
    Extract and display metadata from a PDF file, including our custom DataObject metadata.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary containing all extracted metadata
    """
    try:
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
        logger.info(f"Reading PDF: {pdf_path}")
        pdf_reader = PdfReader(pdf_path)
        
        # Get standard PDF metadata
        metadata = {
            "Standard Metadata": {
                "Title": pdf_reader.metadata.get("/Title"),
                "Author": pdf_reader.metadata.get("/Author"),
                "Subject": pdf_reader.metadata.get("/Subject"),
                "Keywords": pdf_reader.metadata.get("/Keywords"),
                "Creator": pdf_reader.metadata.get("/Creator"),
                "Producer": pdf_reader.metadata.get("/Producer"),
                "CreationDate": pdf_reader.metadata.get("/CreationDate"),
                "ModDate": pdf_reader.metadata.get("/ModDate")
            }
        }
        
        # Get our custom DataObject metadata
        if "/DataObject" in pdf_reader.metadata:
            try:
                data_object = json.loads(pdf_reader.metadata["/DataObject"])
                metadata["DataObject"] = data_object
            except json.JSONDecodeError:
                logger.warning("Could not parse DataObject metadata as JSON")
                metadata["DataObject"] = pdf_reader.metadata["/DataObject"]
        
        # Add additional useful information
        metadata["Additional Info"] = {
            "Page Count": len(pdf_reader.pages),
            "File Size": pdf_path.stat().st_size,
            "File Path": str(pdf_path)
        }
        
        return metadata
    
    except Exception as e:
        logger.error(f"Error extracting metadata: {str(e)}")
        raise

def main():
    if len(sys.argv) != 2:
        print("Usage: python dump_pdf_metadata.py <pdf_file>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    try:
        metadata = dump_pdf_metadata(pdf_path)
        print("\nPDF Metadata:")
        print("=" * 50)
        print(json.dumps(metadata, indent=2))
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()