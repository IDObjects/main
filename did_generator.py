from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import base58
import json
from typing import Dict, Tuple, Optional, Union
import sys
from dataclasses import dataclass

@dataclass
class DIDKeyPair:
    did: str
    document: dict
    private_key: bytes
    public_key: bytes

def generate_ed25519_keypair() -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
    """Generate an Ed25519 key pair."""
    try:
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return private_key, public_key
    except Exception as e:
        print(f"Error generating key pair: {e}", file=sys.stderr)
        raise

def encode_multibase(key_bytes: bytes) -> str:
    """Encode bytes using base58btc multibase encoding."""
    try:
        return 'z' + base58.b58encode(key_bytes).decode('utf-8')
    except Exception as e:
        print(f"Error encoding key: {e}", file=sys.stderr)
        raise

def sign_data(private_key: Union[ed25519.Ed25519PrivateKey, bytes], data: bytes) -> str:
    """Sign data using a private key."""
    try:
        if isinstance(private_key, bytes):
            private_key = serialization.load_pem_private_key(
                private_key,
                password=b'your-secure-password',
            )
        signature = private_key.sign(data)
        return base58.b58encode(signature).decode('utf-8')
    except Exception as e:
        print(f"Error signing data: {e}", file=sys.stderr)
        raise

def verify_signature(public_key: Union[ed25519.Ed25519PublicKey, bytes], signature: str, data: bytes) -> bool:
    """Verify a signature using a public key."""
    try:
        if isinstance(public_key, bytes):
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key)
        signature_bytes = base58.b58decode(signature)
        public_key.verify(signature_bytes, data)
        return True
    except Exception as e:
        print(f"Signature verification failed: {e}", file=sys.stderr)
        return False

def generate_did_key(parent_did: Optional[str] = None, parent_private_key: Optional[bytes] = None) -> Dict:
    """Generate a DID:key identifier, optionally signed by a parent DID.
    
    Args:
        parent_did: Optional parent DID that will sign the new DID
        parent_private_key: Private key of the parent DID for signing
        
    Returns:
        Dictionary containing the DID, document, and private key
    """
    try:
        # Generate key pair for the new DID
        private_key, public_key = generate_ed25519_keypair()
        
        # Get public key bytes
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        # Encode public key using multibase
        encoded_public_key = encode_multibase(public_key_bytes)
        
        # Construct DID:key
        did_key = f"did:key:{encoded_public_key}"
        
        # Create DID document
        did_document = {
            "@context": ["https://www.w3.org/ns/did/v1"],
            "id": did_key,
            "verificationMethod": [{
                "id": f"{did_key}#{encoded_public_key}",
                "type": "Ed25519VerificationKey2018",
                "controller": did_key,
                "publicKeyMultibase": encoded_public_key
            }],
            "authentication": [f"{did_key}#{encoded_public_key}"],
            "assertionMethod": [f"{did_key}#{encoded_public_key}"]
        }
        
        # Add parent signature if parent DID and key are provided
        if parent_did and parent_private_key:
            # Create a proof of parent signature
            signature_data = f"{parent_did}:{did_key}".encode('utf-8')
            signature = sign_data(parent_private_key, signature_data)
            
            # Add proof to the DID document
            did_document["proof"] = {
                "type": "Ed25519Signature2018",
                "created": "2025-05-11T13:45:09Z",  # Should be current time in production
                "verificationMethod": f"{parent_did}#{parent_did.split(':')[-1]}",
                "proofPurpose": "assertionMethod",
                "jws": signature
            }
        
        # Export private key with proper encryption
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(b'your-secure-password')
        )
        
        return {
            "did": did_key,
            "document": did_document,
            "private_key": private_key_bytes.hex(),
            "public_key": public_key_bytes.hex()
        }
        
    except Exception as e:
        print(f"Error generating DID: {e}", file=sys.stderr)
        raise

def verify_parent_signature(child_document: dict, parent_public_key: bytes) -> bool:
    """Verify that a child DID document was signed by its parent.
    
    Args:
        child_document: The child DID document to verify
        parent_public_key: The public key of the parent DID
        
    Returns:
        bool: True if the signature is valid, False otherwise
    """
    try:
        if "proof" not in child_document:
            print("No proof found in document", file=sys.stderr)
            return False
            
        proof = child_document["proof"]
        if "jws" not in proof:
            print("No JWS signature found in proof", file=sys.stderr)
            return False
            
        # Reconstruct the signed data
        parent_did = proof["verificationMethod"].split('#')[0]
        child_did = child_document["id"]
        signature_data = f"{parent_did}:{child_did}".encode('utf-8')
        
        # Verify the signature
        return verify_signature(parent_public_key, proof["jws"], signature_data)
        
    except Exception as e:
        print(f"Error verifying parent signature: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    try:
        # Example 1: Generate a root DID (no parent)
        print("Generating root DID...")
        root_did = generate_did_key()
        print("\nRoot DID:", root_did["did"])
        
        # Example 2: Generate a child DID signed by the root DID
        print("\nGenerating child DID signed by root...")
        child_did = generate_did_key(
            parent_did=root_did["did"],
            parent_private_key=bytes.fromhex(root_did["private_key"])
        )
        
        print("\nChild DID:", child_did["did"])
        print("\nChild DID Document:")
        print(json.dumps(child_did["document"], indent=2))
        
        # Verify the parent signature
        print("\nVerifying parent signature...")
        is_valid = verify_parent_signature(
            child_did["document"],
            bytes.fromhex(root_did["public_key"])
        )
        print(f"Parent signature is valid: {is_valid}")
        
    except Exception as e:
        print(f"Error in main execution: {e}", file=sys.stderr)
        sys.exit(1)