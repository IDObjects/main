import sys
import os
import json
import hashlib
import logging
from datetime import datetime, UTC
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter
from data_object import DataObject, ValidityCondition

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pdf_data_object.log')
    ]
)

logger = logging.getLogger(__name__)

def create_pdf_data_object(pdf_path: str, did_document: dict, owner_public_key: str, output_dir: str = None) -> dict:
    """
    Create a data object from a PDF file and embed the metadata.
    
    Args:
        pdf_path: Path to the PDF file
        did_document: The DID document containing the owner's DID and verification methods
        owner_public_key: The owner's public key in PEM format
        output_dir: Optional directory to save the output PDF
        
    Returns:
        Dictionary containing the data object and output file path
    """
    logger.info(f"Creating data object for PDF: {pdf_path}")
    
    try:
        # Extract owner DID from the document
        owner_did = did_document.get("id")
        if not owner_did:
            raise ValueError("DID document is missing 'id' field")
        
        # Read the PDF file
        logger.debug("Reading PDF file")
        pdf_reader = PdfReader(pdf_path)
        
        # Calculate PDF hash
        logger.debug("Calculating PDF hash")
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
            pdf_hash = hashlib.sha256(pdf_content).hexdigest()
        
        # Create content for the data object
        logger.debug("Creating data object content")
        content = {
            "pdf_hash": pdf_hash,
            "page_count": len(pdf_reader.pages),
            "original_filename": os.path.basename(pdf_path),
            "metadata": {
                "created_at": datetime.now(UTC).isoformat(),
                "file_size": os.path.getsize(pdf_path),
                "mime_type": "application/pdf"
            }
        }
        
        # Create validity conditions
        logger.debug("Setting up validity conditions")
        validity_conditions = [
            {
                "type": "expiration",
                "parameters": {
                    "date": datetime.now(UTC).replace(year=datetime.now(UTC).year + 1).isoformat()
                },
                "description": "Document expires in one year"
            }
        ]
        
        # Create the data object
        logger.info("Creating data object")
        data_obj = DataObject.create(
            owner_did=owner_did,
            data_type="pdf_document",
            content=content,
            owner_public_key=owner_public_key,
            validity_conditions=validity_conditions
        )
        
        # Create a copy of the PDF with embedded metadata
        logger.debug("Creating PDF copy with metadata")
        pdf_writer = PdfWriter()
        
        # Copy all pages
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        
        # Add metadata
        metadata = {
            "data_object": data_obj.to_dict(),
            "pdf_hash": pdf_hash,
            "did_document": did_document  # Include the full DID document
        }
        
        pdf_writer.add_metadata({
            "/DataObject": json.dumps(metadata)
        })
        
        # Determine output path
        if output_dir is None:
            output_dir = os.path.dirname(pdf_path)
        
        output_filename = f"data_object_{pdf_hash[:8]}_{os.path.basename(pdf_path)}"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save the new PDF
        logger.info(f"Saving output PDF to: {output_path}")
        with open(output_path, 'wb') as output_file:
            pdf_writer.write(output_file)
        
        logger.info("Data object creation completed successfully")
        return {
            "data_object": data_obj.to_dict(),
            "output_path": output_path,
            "pdf_hash": pdf_hash
        }
    
    except Exception as e:
        logger.error(f"Error creating data object: {str(e)}", exc_info=True)
        raise

def verify_pdf_data_object(pdf_path: str, owner_private_key: str) -> dict:
    """
    Verify a PDF with embedded data object metadata.
    
    Args:
        pdf_path: Path to the PDF file
        owner_private_key: The owner's private key in PEM format
        
    Returns:
        Dictionary containing verification results
    """
    logger.info(f"Verifying PDF data object: {pdf_path}")
    
    try:
        # Read the PDF and its metadata
        logger.debug("Reading PDF metadata")
        pdf_reader = PdfReader(pdf_path)
        metadata = pdf_reader.metadata
        
        if not metadata or "/DataObject" not in metadata:
            logger.warning("No data object metadata found in PDF")
            return {
                "valid": False,
                "error": "No data object metadata found"
            }
        
        # Parse the metadata
        logger.debug("Parsing data object metadata")
        data_object_metadata = json.loads(metadata["/DataObject"])
        data_object_dict = data_object_metadata["data_object"]
        
        # Create DataObject instance
        data_obj = DataObject.from_dict(data_object_dict)
        
        # Verify the PDF hash
        logger.debug("Verifying PDF hash")
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
            current_hash = hashlib.sha256(pdf_content).hexdigest()
        
        if current_hash != data_object_metadata["pdf_hash"]:
            logger.warning("PDF content has been modified")
            return {
                "valid": False,
                "error": "PDF content has been modified"
            }
        
        # Verify the data object
        logger.debug("Verifying data object validity")
        if not data_obj.is_valid():
            logger.warning("Data object is not valid")
            return {
                "valid": False,
                "error": "Data object is not valid"
            }
        
        # Decrypt and verify content
        logger.debug("Decrypting content")
        decrypted_content = data_obj.decrypt_content(owner_private_key)
        
        logger.info("PDF data object verification completed successfully")
        return {
            "valid": True,
            "data_object": data_obj.to_dict(),
            "decrypted_content": decrypted_content
        }
    
    except Exception as e:
        logger.error(f"Error verifying data object: {str(e)}", exc_info=True)
        return {
            "valid": False,
            "error": str(e)
        }

if __name__ == "__main__":
    if len(sys.argv) < 4:
        logger.error("Insufficient arguments provided")
        print("Usage: python pdf_data_object.py <pdf_path> <did_document_path> <public_key_path> [output_dir]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    did_document_path = sys.argv[2]
    public_key_path = sys.argv[3]
    output_dir = sys.argv[4] if len(sys.argv) > 4 else None
    
    logger.info(f"Starting PDF data object creation for: {pdf_path}")
    logger.debug(f"DID document path: {did_document_path}")
    logger.debug(f"Public key path: {public_key_path}")
    logger.debug(f"Output directory: {output_dir}")
    
    # Read the DID document
    try:
        with open(did_document_path, 'r') as f:
            did_document = json.load(f)
        logger.debug("DID document loaded successfully")
    except Exception as e:
        logger.error(f"Error reading DID document: {str(e)}")
        sys.exit(1)
    
    # Read the public key
    try:
        with open(public_key_path, 'r') as f:
            public_key = f.read()
        logger.debug("Public key loaded successfully")
    except Exception as e:
        logger.error(f"Error reading public key: {str(e)}")
        sys.exit(1)
    
    try:
        result = create_pdf_data_object(pdf_path, did_document, public_key, output_dir)
        print("\nData Object Created Successfully:")
        print(f"Output PDF: {result['output_path']}")
        print(f"PDF Hash: {result['pdf_hash']}")
        print("\nData Object:")
        print(json.dumps(result['data_object'], indent=2))
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        sys.exit(1) 