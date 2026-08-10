import hashlib
import secrets

def hash_password(password: str) -> str:
    """Hashes a password using PBKDF2 with SHA256 and a random salt."""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return f"{salt}${pwd_hash}"

def verify_password(password: str, hashed_password: str) -> bool:
    """Verifies a raw password against the stored salt$hash string."""
    try:
        salt, pwd_hash = hashed_password.split('$')
        recomputed_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        return secrets.compare_digest(recomputed_hash, pwd_hash)
    except Exception:
        return False
