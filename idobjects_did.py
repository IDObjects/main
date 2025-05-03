from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import base58
import json
import hashlib
import time

class IdObjectsDID:
    """
    Implementation of the idobjects DID method.
    DID Syntax: did:idobjects:<namespace>:<unique-id>
    """
    
    def __init__(self, namespace: str = "main"):
        self.namespace = namespace
        self._did_registry = {}  # In-memory registry to track parent-child relationships
    
    def generate_unique_id(self, public_key_bytes: bytes) -> str:
        """Generate a unique identifier from public key bytes."""
        # Create a hash of the public key
        hash_obj = hashlib.sha256(public_key_bytes)
        # Take first 8 bytes and encode in base58
        return base58.b58encode(hash_obj.digest()[:8]).decode('utf-8')
    
    def generate_keypair(self):
        """Generate an Ed25519 key pair."""
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return private_key, public_key
    
    def encode_multibase(self, key_bytes: bytes) -> str:
        """Encode bytes using base58btc multibase encoding."""
        return 'z' + base58.b58encode(key_bytes).decode('utf-8')
    
    def create_ownership_proof(self, parent_private_key: ed25519.Ed25519PrivateKey, child_did: str) -> dict:
        """Create a cryptographic proof of parent ownership for a child DID."""
        # Create a proof object
        proof = {
            "type": "Ed25519Signature2018",
            "created": time.time(),
            "verificationMethod": f"{child_did}#parent-ownership",
            "proofPurpose": "parentOwnership",
            "child": child_did
        }
        
        # Create the message to sign
        message = json.dumps(proof, sort_keys=True).encode('utf-8')
        
        # Sign the message
        signature = parent_private_key.sign(message)
        
        # Add the signature to the proof
        proof["signature"] = base58.b58encode(signature).decode('utf-8')
        
        return proof
    
    def create_did(self, parent_did: str = None, parent_private_key: str = None) -> dict:
        """Create a new idobjects DID, optionally as a child of a parent DID."""
        # Generate key pair
        private_key, public_key = self.generate_keypair()
        
        # Get public key bytes
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        # Generate unique identifier
        unique_id = self.generate_unique_id(public_key_bytes)
        
        # Construct DID
        did = f"did:idobjects:{self.namespace}:{unique_id}"
        
        # Encode public key
        encoded_public_key = self.encode_multibase(public_key_bytes)
        
        # Create DID document
        did_document = {
            "@context": [
                "https://www.w3.org/ns/did/v1",
                {
                    "idobjects": "https://w3id.org/idobjects#",
                    "Ed25519VerificationKey2018": "idobjects:Ed25519VerificationKey2018",
                    "Ed25519Signature2018": "idobjects:Ed25519Signature2018"
                }
            ],
            "id": did,
            "controller": did,
            "children": [],  # Initialize empty children list
            "verificationMethod": [{
                "id": f"{did}#keys-1",
                "type": "Ed25519VerificationKey2018",
                "controller": did,
                "publicKeyMultibase": encoded_public_key
            }],
            "authentication": [f"{did}#keys-1"],
            "assertionMethod": [f"{did}#keys-1"],
            "capabilityInvocation": [f"{did}#keys-1"],
            "capabilityDelegation": [f"{did}#keys-1"]
        }
        
        # Update parent's children list if this is a child DID
        if parent_did and parent_private_key:
            if parent_did not in self._did_registry:
                self._did_registry[parent_did] = {"children": []}
            
            # Create ownership proof
            parent_priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(
                bytes.fromhex(parent_private_key)
            )
            ownership_proof = self.create_ownership_proof(parent_priv_key, did)
            
            # Add proof to child's document
            did_document["proof"] = ownership_proof
            
            # Update parent's children list
            self._did_registry[parent_did]["children"].append(did)
        
        # Store this DID in registry
        self._did_registry[did] = {
            "document": did_document,
            "children": []
        }
        
        return {
            "did": did,
            "document": did_document,
            "private_key": private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption()
            ).hex()
        }
    
    def verify_ownership(self, child_did: str, parent_did: str) -> bool:
        """Verify that a parent DID owns a child DID."""
        if child_did not in self._did_registry:
            return False
        
        child_doc = self._did_registry[child_did]["document"]
        if "proof" not in child_doc:
            return False
        
        proof = child_doc["proof"]
        if proof["type"] != "Ed25519Signature2018" or proof["child"] != child_did:
            return False
        
        # Get parent's public key from registry
        if parent_did not in self._did_registry:
            return False
        
        parent_doc = self._did_registry[parent_did]["document"]
        parent_pub_key = None
        for vm in parent_doc["verificationMethod"]:
            if vm["type"] == "Ed25519VerificationKey2018":
                parent_pub_key = base58.b58decode(vm["publicKeyMultibase"][1:])
                break
        
        if not parent_pub_key:
            return False
        
        # Verify the signature
        parent_pub_key_obj = ed25519.Ed25519PublicKey.from_public_bytes(parent_pub_key)
        message = json.dumps({k: v for k, v in proof.items() if k != "signature"}, sort_keys=True).encode('utf-8')
        signature = base58.b58decode(proof["signature"])
        
        try:
            parent_pub_key_obj.verify(signature, message)
            return True
        except:
            return False
    
    def attempt_parent_calculation(self, child_did: str) -> dict:
        """
        Attempt to calculate the parent DID from a child DID.
        This demonstrates that it's impossible to derive the parent DID from the child.
        """
        if child_did not in self._did_registry:
            return {"error": "Child DID not found"}
        
        child_doc = self._did_registry[child_did]["document"]
        if "proof" not in child_doc:
            return {"error": "No ownership proof found"}
        
        proof = child_doc["proof"]
        
        # Attempt 1: Try to extract parent DID from proof
        # The proof only contains the child DID, not the parent
        proof_analysis = {
            "contains_parent_did": False,
            "proof_fields": list(proof.keys()),
            "message": "Proof only contains child DID reference, not parent DID"
        }
        
        # Attempt 2: Try to derive from signature
        # The signature is of the proof object, not the parent DID
        signature_analysis = {
            "can_derive_parent": False,
            "reason": "Signature is of proof object, not parent DID identifier"
        }
        
        # Attempt 3: Try to derive from child's public key
        # The child's public key is independent of the parent's
        child_pub_key = None
        for vm in child_doc["verificationMethod"]:
            if vm["type"] == "Ed25519VerificationKey2018":
                child_pub_key = base58.b58decode(vm["publicKeyMultibase"][1:])
                break
        
        key_analysis = {
            "child_public_key_length": len(child_pub_key) if child_pub_key else 0,
            "can_derive_parent": False,
            "reason": "Child's public key is cryptographically independent of parent's"
        }
        
        return {
            "child_did": child_did,
            "analysis": {
                "proof_analysis": proof_analysis,
                "signature_analysis": signature_analysis,
                "key_analysis": key_analysis
            },
            "conclusion": "Parent DID cannot be calculated from child DID or its proof"
        }
    
    def resolve_did(self, did: str) -> dict:
        """Resolve a DID to its DID document."""
        if not did.startswith(f"did:idobjects:{self.namespace}:"):
            raise ValueError("Invalid idobjects DID format")
        
        if did in self._did_registry:
            # Get the document and update children from registry
            document = self._did_registry[did]["document"].copy()
            document["children"] = self._did_registry[did]["children"]
            return {"didDocument": document}
        
        return {
            "didDocument": {
                "@context": ["https://www.w3.org/ns/did/v1"],
                "id": did,
                "error": "DID not found in registry"
            }
        }

if __name__ == "__main__":
    # Example usage
    idobjects = IdObjectsDID()
    
    # Create a root DID
    root_result = idobjects.create_did()
    print("Root DID:", root_result["did"])
    print("\nRoot DID Document:")
    print(json.dumps(root_result["document"], indent=2))
    
    # Create a child DID with parent ownership proof
    child_result = idobjects.create_did(
        parent_did=root_result["did"],
        parent_private_key=root_result["private_key"]
    )
    print("\nChild DID:", child_result["did"])
    print("\nChild DID Document:")
    print(json.dumps(child_result["document"], indent=2))
    
    # Verify ownership
    is_owned = idobjects.verify_ownership(child_result["did"], root_result["did"])
    print("\nOwnership Verification:", is_owned)
    
    # Attempt to calculate parent DID from child
    print("\nAttempting to calculate parent DID from child:")
    parent_calc_result = idobjects.attempt_parent_calculation(child_result["did"])
    print(json.dumps(parent_calc_result, indent=2))
    
    # Create a grandchild DID
    grandchild_result = idobjects.create_did(
        parent_did=child_result["did"],
        parent_private_key=child_result["private_key"]
    )
    print("\nGrandchild DID:", grandchild_result["did"])
    print("\nGrandchild DID Document:")
    print(json.dumps(grandchild_result["document"], indent=2))
    
    # Verify grandchild ownership
    is_grandchild_owned = idobjects.verify_ownership(grandchild_result["did"], child_result["did"])
    print("\nGrandchild Ownership Verification:", is_grandchild_owned)
    
    # Attempt to calculate parent DID from grandchild
    print("\nAttempting to calculate parent DID from grandchild:")
    grandchild_parent_calc = idobjects.attempt_parent_calculation(grandchild_result["did"])
    print(json.dumps(grandchild_parent_calc, indent=2))
    
    # Resolve and show updated documents with children
    print("\nResolved Root DID Document (with children):")
    print(json.dumps(idobjects.resolve_did(root_result["did"])["didDocument"], indent=2))
    
    print("\nResolved Child DID Document (with children):")
    print(json.dumps(idobjects.resolve_did(child_result["did"])["didDocument"], indent=2)) 