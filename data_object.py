from dataclasses import dataclass
import hashlib
import json
from datetime import datetime
from typing import Any, Dict, Optional, List
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import padding as sym_padding
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
import base64
import os

@dataclass(frozen=True)
class ValidityCondition:
    """
    A condition that must be met for the data object to be valid.
    """
    condition_type: str
    parameters: Dict[str, Any]
    description: str

@dataclass(frozen=True)
class DataObject:
    """
    An immutable data object that contains:
    - Hash of the DID owner
    - Data type
    - Content blob
    - Encrypted content blob
    - Creation timestamp
    - Hash of the content blob
    - State (active, invalid)
    - Validity conditions
    """
    owner_did_hash: str
    data_type: str
    content: Dict[str, Any]
    encrypted_content: str
    created_at: datetime
    content_hash: str
    state: str
    validity_conditions: List[ValidityCondition]

    @classmethod
    def create(
        cls,
        owner_did: str,
        data_type: str,
        content: Dict[str, Any],
        owner_public_key: str,
        validity_conditions: Optional[List[Dict[str, Any]]] = None
    ) -> 'DataObject':
        """
        Create a new DataObject using hybrid encryption.
        
        Args:
            owner_did: The DID of the owner
            data_type: The type of data being stored
            content: The content to be stored (must be JSON-serializable)
            owner_public_key: The owner's public key in PEM format
            validity_conditions: Optional list of validity conditions
            
        Returns:
            A new immutable DataObject instance
        """
        # Calculate owner DID hash
        owner_hash = hashlib.sha256(owner_did.encode('utf-8')).hexdigest()
        
        # Get current timestamp
        created_at = datetime.utcnow()
        
        # Calculate content hash
        content_json = json.dumps(content, sort_keys=True).encode('utf-8')
        content_hash = hashlib.sha256(content_json).hexdigest()
        
        # Generate a random AES key
        aes_key = os.urandom(32)  # 256-bit key
        
        # Encrypt content using AES
        iv = os.urandom(16)  # 128-bit IV
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        
        # Pad the content
        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(content_json) + padder.finalize()
        
        # Encrypt the padded data
        encrypted_content = encryptor.update(padded_data) + encryptor.finalize()
        
        # Encrypt the AES key using RSA
        public_key = RSA.import_key(owner_public_key)
        cipher_rsa = PKCS1_OAEP.new(public_key)
        encrypted_aes_key = cipher_rsa.encrypt(aes_key)
        
        # Combine encrypted content and encrypted key
        encrypted_data = {
            "encrypted_content": base64.b64encode(encrypted_content).decode('utf-8'),
            "encrypted_key": base64.b64encode(encrypted_aes_key).decode('utf-8'),
            "iv": base64.b64encode(iv).decode('utf-8')
        }
        
        # Initialize validity conditions
        if validity_conditions is None:
            validity_conditions = []
        
        # Convert validity conditions to ValidityCondition objects
        conditions = [
            ValidityCondition(
                condition_type=cond["type"],
                parameters=cond.get("parameters", {}),
                description=cond.get("description", "")
            )
            for cond in validity_conditions
        ]
        
        return cls(
            owner_did_hash=owner_hash,
            data_type=data_type,
            content=content,
            encrypted_content=json.dumps(encrypted_data),
            created_at=created_at,
            content_hash=content_hash,
            state="active",
            validity_conditions=conditions
        )
    
    def decrypt_content(self, owner_private_key: str) -> Dict[str, Any]:
        """
        Decrypt the content using the owner's private key.
        
        Args:
            owner_private_key: The owner's private key in PEM format
            
        Returns:
            The decrypted content as a dictionary
        """
        encrypted_data = json.loads(self.encrypted_content)
        encrypted_aes_key = base64.b64decode(encrypted_data["encrypted_key"])
        encrypted_content = base64.b64decode(encrypted_data["encrypted_content"])
        iv = base64.b64decode(encrypted_data["iv"])
        
        private_key = RSA.import_key(owner_private_key)
        cipher_rsa = PKCS1_OAEP.new(private_key)
        aes_key = cipher_rsa.decrypt(encrypted_aes_key)
        
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        
        decrypted_padded_data = decryptor.update(encrypted_content) + decryptor.finalize()
        
        unpadder = sym_padding.PKCS7(128).unpadder()
        decrypted_content = unpadder.update(decrypted_padded_data) + unpadder.finalize()
        
        return json.loads(decrypted_content.decode('utf-8'))
    
    def verify_owner(self, owner_did: str) -> bool:
        """
        Verify if the given DID matches the owner hash.
        
        Args:
            owner_did: The DID to verify
            
        Returns:
            True if the DID matches the owner hash, False otherwise
        """
        return hashlib.sha256(owner_did.encode('utf-8')).hexdigest() == self.owner_did_hash
    
    def verify_content(self) -> bool:
        """
        Verify if the content hash matches the current content.
        
        Returns:
            True if the content hash is valid, False otherwise
        """
        content_json = json.dumps(self.content, sort_keys=True).encode('utf-8')
        return hashlib.sha256(content_json).hexdigest() == self.content_hash
    
    def is_valid(self) -> bool:
        """
        Check if the data object is valid based on its state and validity conditions.
        
        Returns:
            True if the object is valid, False otherwise
        """
        if self.state != "active":
            return False
        
        # Check validity conditions
        for condition in self.validity_conditions:
            if condition.condition_type == "expiration":
                expiration_date = datetime.fromisoformat(condition.parameters["date"])
                if datetime.utcnow() > expiration_date:
                    return False
            elif condition.condition_type == "version":
                if "min_version" in condition.parameters:
                    if self.content.get("version", "0") < condition.parameters["min_version"]:
                        return False
            # Add more condition types as needed
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the DataObject to a dictionary.
        
        Returns:
            A dictionary representation of the DataObject
        """
        return {
            "owner_did_hash": self.owner_did_hash,
            "data_type": self.data_type,
            "content": self.content,
            "encrypted_content": self.encrypted_content,
            "created_at": self.created_at.isoformat(),
            "content_hash": self.content_hash,
            "state": self.state,
            "validity_conditions": [
                {
                    "type": cond.condition_type,
                    "parameters": cond.parameters,
                    "description": cond.description
                }
                for cond in self.validity_conditions
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataObject':
        """
        Create a DataObject from a dictionary.
        
        Args:
            data: Dictionary containing the DataObject fields
            
        Returns:
            A new DataObject instance
        """
        validity_conditions = [
            ValidityCondition(
                condition_type=cond["type"],
                parameters=cond["parameters"],
                description=cond["description"]
            )
            for cond in data["validity_conditions"]
        ]
        
        return cls(
            owner_did_hash=data["owner_did_hash"],
            data_type=data["data_type"],
            content=data["content"],
            encrypted_content=data["encrypted_content"],
            created_at=datetime.fromisoformat(data["created_at"]),
            content_hash=data["content_hash"],
            state=data["state"],
            validity_conditions=validity_conditions
        )

if __name__ == "__main__":
    # Example usage
    from Crypto.PublicKey import RSA
    
    # Generate a key pair for encryption
    key = RSA.generate(2048)
    private_key = key.export_key().decode('utf-8')
    public_key = key.publickey().export_key().decode('utf-8')
    
    # Create a mock DID
    owner_did = "did:example:123456789"
    
    # Define validity conditions
    validity_conditions = [
        {
            "type": "expiration",
            "parameters": {
                "date": (datetime.utcnow().replace(year=datetime.utcnow().year + 1)).isoformat()
            },
            "description": "Data expires in one year"
        },
        {
            "type": "version",
            "parameters": {
                "min_version": "1.0"
            },
            "description": "Minimum version requirement"
        }
    ]
    
    # Create a data object
    content = {
        "name": "Example Data",
        "value": 42,
        "version": "1.1",
        "metadata": {
            "version": "1.0",
            "tags": ["test", "example"]
        }
    }
    
    data_obj = DataObject.create(
        owner_did=owner_did,
        data_type="example_data",
        content=content,
        owner_public_key=public_key,
        validity_conditions=validity_conditions
    )
    
    # Print the data object
    print("Data Object:")
    print(json.dumps(data_obj.to_dict(), indent=2))
    
    # Verify owner
    print("\nOwner Verification:")
    print(f"Valid owner: {data_obj.verify_owner(owner_did)}")
    print(f"Invalid owner: {data_obj.verify_owner('did:example:123')}")
    
    # Verify content
    print("\nContent Verification:")
    print(f"Content valid: {data_obj.verify_content()}")
    
    # Check validity
    print("\nValidity Check:")
    print(f"Object valid: {data_obj.is_valid()}")
    
    # Decrypt content
    print("\nDecrypted Content:")
    decrypted_content = data_obj.decrypt_content(private_key)
    print(json.dumps(decrypted_content, indent=2))
    
    # Try to modify the object (will raise an error)
    try:
        data_obj.content["name"] = "Modified"  # This will raise an error
    except Exception as e:
        print(f"\nAttempt to modify content failed: {e}") 