"""
Password hashing utilities using passlib.

This module provides password hashing functionality using passlib with 
pbkdf2_sha256 as the default backend, which is pure Python and works
on cPanel/shared hosting without requiring C compilation.

For desktop environments where bcrypt is available, bcrypt can be used
by installing requirements-desktop.txt.
"""
from passlib.hash import pbkdf2_sha256


def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2-SHA256.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
    """
    return pbkdf2_sha256.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against a hash.
    
    Supports both:
    - PBKDF2-SHA256 hashes (passlib format: $pbkdf2-sha256$...)
    - bcrypt hashes (for backward compatibility: $2b$...)
    
    Args:
        password: Plain text password to verify
        hashed: Hashed password to check against
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        # Check if this is a bcrypt hash (starts with $2a$, $2b$, or $2y$)
        if hashed.startswith(('$2a$', '$2b$', '$2y$')):
            # Try to use bcrypt if available (desktop environment)
            try:
                import bcrypt
                return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
            except ImportError:
                # bcrypt not available, try passlib's bcrypt support
                try:
                    from passlib.hash import bcrypt as passlib_bcrypt
                    return passlib_bcrypt.verify(password, hashed)
                except (ImportError, ValueError):
                    # If bcrypt verification fails, return False
                    # User will need to reset password
                    print("Warning: bcrypt hash detected but bcrypt library not available")
                    return False
        
        # Use PBKDF2-SHA256 for verification
        return pbkdf2_sha256.verify(password, hashed)
        
    except Exception as e:
        print(f"Password verification error: {e}")
        return False


def needs_rehash(hashed: str) -> bool:
    """
    Check if a password hash should be upgraded to the new format.
    
    Returns True if the hash is using bcrypt (old format) and should
    be migrated to PBKDF2-SHA256 for cPanel compatibility.
    
    Args:
        hashed: The hashed password to check
        
    Returns:
        True if password should be rehashed after successful login
    """
    # bcrypt hashes start with $2a$, $2b$, or $2y$
    return hashed.startswith(('$2a$', '$2b$', '$2y$'))
