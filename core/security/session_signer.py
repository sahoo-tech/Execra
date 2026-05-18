import os
import json
import base64
from pathlib import Path
from datetime import datetime, timezone
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

class SessionSigner:
    def __init__(self, key_path: str = None):
        """Initializes the signer, allowing a custom path for testing."""
        if key_path:
            self.key_path = Path(key_path)
        else:
            self.key_path = Path.home() / ".execra" / "session.key"
            
        self._load_or_generate_key()

    def _load_or_generate_key(self) -> None:
        """Loads an existing key or securely generates a new one."""
        if self.key_path.exists():
            with open(self.key_path, "rb") as f:
                key_bytes = f.read()
            self._private_key = serialization.load_pem_private_key(key_bytes, password=None)
        else:
            self.key_path.parent.mkdir(parents=True, exist_ok=True)
            self._private_key = ed25519.Ed25519PrivateKey.generate()
            
            key_bytes = self._private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            with open(self.key_path, "wb") as f:
                f.write(key_bytes)
            
            # chmod 600 ensures only the file owner can read or write the key
            os.chmod(self.key_path, 0o600)

    def _serialize_record(self, record) -> bytes:
        """Converts records to a strict, alphabetically sorted JSON string."""
        if hasattr(record, "model_dump"):
            record_dict = record.model_dump()
        elif hasattr(record, "dict"):
            record_dict = record.dict()
        elif hasattr(record, "__dict__"):
            record_dict = record.__dict__
        elif isinstance(record, dict):
            record_dict = record
        else:
            record_dict = dict(record)

        # sort_keys=True is mandatory so the hash doesn't change randomly
        json_str = json.dumps(record_dict, sort_keys=True, separators=(',', ':'))
        return json_str.encode('utf-8')

    def sign(self, record) -> str:
        """Signs the record and returns a base64 encoded signature."""
        data_bytes = self._serialize_record(record)
        signature_bytes = self._private_key.sign(data_bytes)
        return base64.b64encode(signature_bytes).decode('utf-8')

    def verify(self, record, signature: str) -> bool:
        """Verifies the signature, returning False if tampering is detected."""
        try:
            data_bytes = self._serialize_record(record)
            signature_bytes = base64.b64decode(signature.encode('utf-8'))
            
            public_key = self._private_key.public_key()
            public_key.verify(signature_bytes, data_bytes)
            return True
        except (InvalidSignature, Exception):
            return False
    def sign_session_export(self, export_dict: dict) -> dict:
        """Adds a session-level signature and timestamp to an export dictionary."""
        # Inject the ISO8601 timestamp requested in the issue
        export_dict["signed_at"] = datetime.now(timezone.utc).isoformat()
        
        # Strip out any pre-existing signature key so we don't accidentally sign a previous signature
        clean_dict = {k: v for k, v in export_dict.items() if k != "signature"}
        
        export_dict["signature"] = self.sign(clean_dict)
        return export_dict

    def verify_session_export(self, export_dict: dict) -> bool:
        """Extracts and verifies the top-level session export signature."""
        signature = export_dict.get("signature")
        if not signature:
            return False
        
        # Remove the signature to reconstruct the exact data payload that was signed
        clean_dict = {k: v for k, v in export_dict.items() if k != "signature"}
        return self.verify(clean_dict, signature)

    def rotate_key(self, db_connection=None) -> None:
        """Generates a new key, replaces the old key safely, and re-signs DB records."""
        #Generate the brand new key
        new_private_key = ed25519.Ed25519PrivateKey.generate()
        
        #Re-sign existing historical records if a DB connection is provided
        if db_connection:
            cursor = db_connection.cursor()
            # Fetch all items needing a re-sign
            cursor.execute("SELECT id, user_id, action, timestamp FROM action_log")
            rows = cursor.fetchall()
            
            for row in rows:
                row_id = row[0]
                record_data = {
                    "user_id": row[1],
                    "action": row[2],
                    "timestamp": row[3]
                }
                
                # Sign with the NEW key
                json_str = json.dumps(record_data, sort_keys=True, separators=(',', ':'))
                new_sig_bytes = new_private_key.sign(json_str.encode('utf-8'))
                new_signature = base64.b64encode(new_sig_bytes).decode('utf-8')
                
                cursor.execute(
                    "UPDATE action_log SET signature = ? WHERE id = ?",
                    (new_signature, row_id)
                )
            db_connection.commit()

        #Replace the key file safely on disk
        new_key_bytes = new_private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Write to a temp file first, then atomic replace to prevent data loss mid-write
        tmp_path = self.key_path.with_suffix('.tmp')
        with open(tmp_path, "wb") as f:
            f.write(new_key_bytes)
        os.chmod(tmp_path, 0o600)
        os.replace(tmp_path, self.key_path)
        
        # Swap the class instance to use the new key
        self._private_key = new_private_key