from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import base58
import json
from typing import Dict, Tuple
import sys

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

def generate_did_key() -> Dict:
    """Generate a DID:key identifier."""
    try:
        # Generate key pair
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
        
        # Export private key with proper encryption
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(b'your-secure-password')
        )
        
        return {
            "did": did_key,
            "document": did_document,
            "private_key": private_key_bytes.hex()
        }
        
    except Exception as e:
        print(f"Error generating DID: {e}", file=sys.stderr)
        raise

if __name__ == "__main__":
    try:
        # Generate a DID:key
        result = generate_did_key()
        
        # Print the results
        print("DID:", result["did"])
        print("\nDID Document:")
        print(json.dumps(result["document"], indent=2))
        print("\nPrivate Key (hex):", result["private_key"])
    except Exception as e:
        print(f"Error in main execution: {e}", file=sys.stderr)
        sys.exit(1)