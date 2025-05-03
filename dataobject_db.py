import sqlite3
import json
from typing import Dict, Any, Optional
from pathlib import Path
import uuid
from datetime import datetime

class DataObjectDB:
    def __init__(self, db_path: str = "dataobjects.db"):
        """
        Initialize the DataObject database.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self._initialize_db()
    
    def _initialize_db(self):
        """Create the database and table if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dataobjects (
                    uuid TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    data_object TEXT NOT NULL,
                    pdf_hash TEXT NOT NULL,
                    did_document TEXT NOT NULL
                )
            ''')
            conn.commit()
    
    def store_dataobject(self, 
                         data_object: Dict[str, Any],
                         pdf_hash: str,
                         did_document: Dict[str, Any]) -> str:
        """
        Store a DataObject in the database.
        
        Args:
            data_object: The data object dictionary
            pdf_hash: The hash of the original PDF
            did_document: The DID document associated with the data object
            
        Returns:
            The UUID assigned to this data object
        """
        data_uuid = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO dataobjects (uuid, created_at, data_object, pdf_hash, did_document)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                data_uuid,
                created_at,
                json.dumps(data_object),
                pdf_hash,
                json.dumps(did_document)
            ))
            conn.commit()
        
        return data_uuid
    
    def get_dataobject(self, uuid: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a DataObject by its UUID.
        
        Args:
            uuid: The UUID of the data object
            
        Returns:
            The data object dictionary if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT data_object FROM dataobjects WHERE uuid = ?
            ''', (uuid,))
            result = cursor.fetchone()
            if result:
                return json.loads(result[0])
            return None
    
    def get_pdf_hash(self, uuid: str) -> Optional[str]:
        """
        Retrieve the PDF hash for a data object.
        
        Args:
            uuid: The UUID of the data object
            
        Returns:
            The PDF hash if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT pdf_hash FROM dataobjects WHERE uuid = ?
            ''', (uuid,))
            result = cursor.fetchone()
            if result:
                return result[0]
            return None
    
    def get_did_document(self, uuid: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the DID document for a data object.
        
        Args:
            uuid: The UUID of the data object
            
        Returns:
            The DID document if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT did_document FROM dataobjects WHERE uuid = ?
            ''', (uuid,))
            result = cursor.fetchone()
            if result:
                return json.loads(result[0])
            return None
    
    def list_dataobjects(self, limit: int = 100) -> list:
        """
        List all data objects in the database.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of data object dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT uuid, created_at, data_object, pdf_hash, did_document
                FROM dataobjects
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            results = cursor.fetchall()
            return [{
                "uuid": row[0],
                "created_at": row[1],
                "data_object": json.loads(row[2]),
                "pdf_hash": row[3],
                "did_document": json.loads(row[4])
            } for row in results]