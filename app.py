import streamlit as st
import os
import json
from datetime import datetime
from pathlib import Path
from pdf_data_object import create_pdf_data_object
import base64
from PyPDF2 import PdfReader
import logging
from did_generator import generate_did_key
from cryptography.hazmat.primitives import serialization

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Function to encode file content as base64
def encode_file_to_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def dump_pdf_metadata(pdf_path: str) -> dict:
    """
    Extract and display metadata from a PDF file, including our custom DataObject metadata.
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

def create_child_did(parent_did: str, parent_private_key: str, child_index: int) -> dict:
    """
    Create a child DID based on a parent DID and its private key.
    """
    try:
        # Load parent private key
        private_key = serialization.load_pem_private_key(
            parent_private_key.encode(),
            password=b'your-secure-password',
            backend=None
        )
        
        # Generate child key pair
        child_private_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        child_public_key = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Create child DID
        child_did = f"{parent_did}:{child_index}"
        
        # Create child DID document
        child_document = {
            "@context": ["https://www.w3.org/ns/did/v1"],
            "id": child_did,
            "verificationMethod": [{
                "id": f"{child_did}#keys-1",
                "type": "Ed25519VerificationKey2018",
                "controller": child_did,
                "publicKeyPem": child_public_key.decode()
            }],
            "authentication": [f"{child_did}#keys-1"],
            "assertionMethod": [f"{child_did}#keys-1"],
            "controller": parent_did
        }
        
        return {
            "did": child_did,
            "document": child_document,
            "private_key": child_private_key.decode()
        }
        
    except Exception as e:
        logger.error(f"Error creating child DID: {str(e)}")
        raise

def main():
    st.title("PDF Data Object Generator")
    
    tab1, tab2, tab3 = st.tabs(["Create Data Object", "View Metadata", "Generate DID"])
    
    with tab1:
        # File uploader for PDF
        uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
        
        # File uploader for public key
        public_key = st.file_uploader("Choose your public key (.pem)", type=["pem"])
        
        # Owner DID input
        owner_did = st.text_input("Enter your Owner DID", value="zCgLiFUd5Ju488tASR1aSpyTQVVNGWNGg4xVxBJzDEqCH")
        
        # Output directory
        output_dir = st.text_input("Output Directory (optional)", value="output")
        
        if st.button("Create Data Object"):
            if not uploaded_file:
                st.error("Please upload a PDF file")
                return
                
            if not public_key:
                st.error("Please upload your public key")
                return
                
            if not owner_did:
                st.error("Please enter your Owner DID")
                return
                
            # Create output directory if it doesn't exist
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                
            try:
                # Save uploaded files temporarily
                pdf_path = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                key_path = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pem"
                
                with open(pdf_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                    
                with open(key_path, 'wb') as f:
                    f.write(public_key.getbuffer())
                
                # Read the public key content
                with open(key_path, 'rb') as f:
                    public_key_content = f.read()
                
                # Create data object
                result = create_pdf_data_object(pdf_path, owner_did, public_key_content.decode('utf-8'), output_dir)
                
                # Display results
                st.success("Data Object Created Successfully!")
                st.json(json.loads(result))
                
                # Find the output PDF
                output_pdf = None
                if output_dir:
                    for file in os.listdir(output_dir):
                        if file.startswith("data_object_") and file.endswith(".pdf"):
                            output_pdf = os.path.join(output_dir, file)
                            break
                else:
                    for file in os.listdir():
                        if file.startswith("data_object_") and file.endswith(".pdf"):
                            output_pdf = file
                            break
                
                if output_pdf:
                    # Create download link for the output PDF
                    with open(output_pdf, 'rb') as f:
                        pdf_bytes = f.read()
                    b64_pdf = base64.b64encode(pdf_bytes).decode()
                    href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="{output_pdf}">Download Output PDF</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"Error creating data object: {str(e)}")
                
            finally:
                # Clean up temporary files
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                if os.path.exists(key_path):
                    os.remove(key_path)
    
    with tab2:
        st.header("View PDF Metadata")
        
        # File uploader for viewing metadata
        metadata_file = st.file_uploader("Choose a PDF file to view metadata", type=["pdf"])
        
        if st.button("View Metadata"):
            if not metadata_file:
                st.error("Please upload a PDF file")
                return
                
            try:
                # Save uploaded file temporarily
                temp_pdf_path = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_metadata.pdf"
                with open(temp_pdf_path, 'wb') as f:
                    f.write(metadata_file.getbuffer())
                    
                # Extract and display metadata
                metadata = dump_pdf_metadata(temp_pdf_path)
                st.json(metadata)
                
            except Exception as e:
                st.error(f"Error viewing metadata: {str(e)}")
            
            finally:
                # Clean up temporary file
                if os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)

    with tab3:
        st.header("DID Management")
        
        # Generate new DID section
        st.subheader("Generate New DID")
        if st.button("Generate DID"):
            try:
                result = generate_did_key()
                st.success("DID Generated Successfully!")
                
                # Display results
                st.subheader("DID")
                st.code(result["did"])
                
                st.subheader("DID Document")
                st.json(result["document"])
                
                # Add download buttons
                st.download_button(
                    label="Download DID Document",
                    data=json.dumps(result["document"], indent=2),
                    file_name="did_document.json",
                    mime="application/json"
                )
                
                # Extract public key from the document
                public_key_pem = result["document"]["verificationMethod"][0]["publicKeyPem"]
                
                # Add download button for public key
                st.download_button(
                    label="Download Public Key",
                    data=public_key_pem,
                    file_name="public_key.pem",
                    mime="application/x-pem-file"
                )
                
                st.download_button(
                    label="Download Private Key",
                    data=result["private_key"],
                    file_name="private_key.pem",
                    mime="application/x-pem-file"
                )
                
            except Exception as e:
                st.error(f"Error generating DID: {str(e)}")
        
        # Create child DID section
        st.subheader("Create Child DID")
        
        # File uploaders for parent DID and private key
        did_document = st.file_uploader("Upload Parent DID Document (JSON)", type=["json"])
        private_key_file = st.file_uploader("Upload Parent Private Key (PEM)", type=["pem"])
        child_index = st.number_input("Child Index", min_value=1, value=1)
        
        if st.button("Create Child DID"):
            if not did_document or not private_key_file:
                st.error("Please upload both the DID document and private key")
                return
                
            try:
                # Load parent DID document
                parent_document = json.loads(did_document.read().decode())
                parent_did = parent_document["id"]
                
                # Load parent private key
                parent_private_key = private_key_file.read().decode()
                
                # Create child DID
                result = create_child_did(parent_did, parent_private_key, child_index)
                st.success("Child DID Created Successfully!")
                
                # Display results
                st.subheader("Child DID")
                st.code(result["did"])
                
                st.subheader("Child DID Document")
                st.json(result["document"])
                
                # Add download buttons for child DID
                st.download_button(
                    label="Download Child DID Document",
                    data=json.dumps(result["document"], indent=2),
                    file_name=f"child_did_{child_index}_document.json",
                    mime="application/json"
                )
                
                st.download_button(
                    label="Download Child Private Key",
                    data=result["private_key"],
                    file_name=f"child_did_{child_index}_private_key.pem",
                    mime="application/x-pem-file"
                )
                
            except Exception as e:
                st.error(f"Error creating child DID: {str(e)}")

if __name__ == "__main__":
    main()