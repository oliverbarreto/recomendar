"""
JWT token management service
"""
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import threading
import hashlib
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenBlacklist:
    """Simple in-memory token blacklist for logout functionality"""
    def __init__(self):
        self._blacklisted_tokens: set[str] = set()

    def add_token(self, jti: str) -> None:
        """Add token to blacklist"""
        self._blacklisted_tokens.add(jti)

    def is_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted"""
        return jti in self._blacklisted_tokens

    def cleanup_expired(self) -> None:
        """Cleanup expired tokens (placeholder for future implementation)"""
        # In a production system, you'd want to cleanup expired tokens
        # This could be implemented with a background task
        pass


# Global token blacklist instance
token_blacklist = TokenBlacklist()


class JWTService:
    """JWT token management service"""

    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = settings.jwt_refresh_token_expire_days

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token

        Args:
            data: Data to encode in token
            expires_delta: Custom expiration time

        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)

        # Add standard claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        })

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT refresh token

        Args:
            data: Data to encode in token
            expires_delta: Custom expiration time (optional)

        Returns:
            Encoded JWT refresh token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)

        # Add standard claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        })

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token

        Args:
            token: JWT token to verify
            token_type: Expected token type ("access" or "refresh")

        Returns:
            Decoded payload if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check token type
            if payload.get("type") != token_type:
                return None

            # Check if token is blacklisted (for access tokens)
            if token_type == "access" and "jti" in payload:
                if token_blacklist.is_blacklisted(payload["jti"]):
                    return None

            return payload

        except JWTError:
            return None

    def get_user_id_from_token(self, token: str) -> Optional[int]:
        """
        Extract user ID from token

        Args:
            token: JWT token

        Returns:
            User ID if valid, None if invalid
        """
        payload = self.verify_token(token)
        if payload:
            return payload.get("sub")
        return None

    def blacklist_token(self, token: str) -> bool:
        """
        Add token to blacklist (for logout)

        Args:
            token: JWT token to blacklist

        Returns:
            True if successful, False if token invalid
        """
        payload = self.verify_token(token)
        if payload and "jti" in payload:
            token_blacklist.add_token(payload["jti"])
            return True
        return False

    def create_sliding_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token with sliding expiration
        
        Sliding tokens extend their expiration time when refreshed, 
        providing better UX while maintaining security.

        Args:
            data: Data to encode in token
            expires_delta: Custom expiration time

        Returns:
            Encoded JWT token with sliding capability
        """
        to_encode = data.copy()
        now = datetime.now(timezone.utc)

        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=self.access_token_expire_minutes)

        # Add standard claims with sliding flag
        to_encode.update({
            "exp": expire,
            "iat": now,
            "type": "access",
            "sliding": True  # Mark as sliding token for activity-based refresh
        })

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def refresh_sliding_token(self, token: str) -> Optional[str]:
        """
        Refresh sliding token if still valid
        
        This extends the token expiration based on user activity,
        maintaining the session without requiring re-authentication.

        Args:
            token: JWT token to refresh

        Returns:
            New token with fresh expiration, or None if invalid
        """
        payload = self.verify_token(token)
        if not payload or not payload.get("sliding"):
            return None
        
        # Create new token with fresh expiration
        return self.create_sliding_token({
            "sub": payload["sub"],
            "email": payload.get("email"),
            "is_admin": payload.get("is_admin", False)
        })

    def create_token_pair(self, user_id: int, additional_claims: Optional[Dict[str, Any]] = None, use_sliding: bool = True, remember_me: bool = False) -> Dict[str, str]:
        """
        Create both access and refresh tokens for a user

        Args:
            user_id: User ID to encode in tokens
            additional_claims: Additional data to include
            use_sliding: Whether to create sliding tokens (default: True)
            remember_me: Whether to create extended refresh token (default: False)

        Returns:
            Dictionary with access_token and refresh_token
        """
        # JWT 'sub' claim must be a string according to RFC 7519
        base_claims = {"sub": str(user_id)}
        if additional_claims:
            base_claims.update(additional_claims)

        # Add unique identifier for access token (for blacklisting)
        access_claims = base_claims.copy()
        access_claims["jti"] = f"{user_id}_{datetime.now(timezone.utc).timestamp()}"

        # Create sliding or standard token based on flag
        if use_sliding:
            access_token = self.create_sliding_token(access_claims)
        else:
            access_token = self.create_access_token(access_claims)
        
        # Create refresh token with extended expiration if remember_me is True
        if remember_me:
            # Get extended expiration from config
            from .config import settings
            refresh_expire_delta = timedelta(days=settings.jwt_refresh_token_extended_expire_days)
            refresh_token = self.create_refresh_token(base_claims, expires_delta=refresh_expire_delta)
        else:
            refresh_token = self.create_refresh_token(base_claims)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60  # seconds
        }


# Password utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    Supports both legacy SHA-256 hashes and new bcrypt hashes for backward compatibility.
    """
    # Check if this looks like a legacy SHA-256 hash (64 hex characters)
    if len(hashed_password) == 64 and all(c in '0123456789abcdef' for c in hashed_password):
        # This is a legacy SHA-256 hash, use legacy verification
        return _verify_legacy_password(plain_password, hashed_password)

    # Otherwise, try with the new bcrypt system
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Final fallback to legacy SHA-256 hash verification
        return _verify_legacy_password(plain_password, hashed_password)


def _verify_legacy_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against legacy SHA-256 hash format.
    This is for backward compatibility with existing users.
    """
    import hashlib

    # Use the same salt as the original User entity
    salt = "labcastarr_salt"
    legacy_hash = hashlib.sha256((plain_password + salt).encode()).hexdigest()
    return legacy_hash == hashed_password


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if len(password) > 128:
        return False, "Password must be less than 128 characters long"

    # Check for at least one letter and one number
    has_letter = any(c.isalpha() for c in password)
    has_number = any(c.isdigit() for c in password)

    if not (has_letter and has_number):
        return False, "Password must contain at least one letter and one number"

    return True, ""


# Global JWT service instance (lazy initialization with thread safety)
_jwt_service_instance: Optional[JWTService] = None
_jwt_service_lock = threading.Lock()


def get_jwt_service() -> JWTService:
    """
    Get JWT service instance with thread-safe lazy initialization.
    This ensures the service is created after environment variables are fully loaded.
    """
    global _jwt_service_instance

    if _jwt_service_instance is None:
        with _jwt_service_lock:
            # Double-check pattern for thread safety
            if _jwt_service_instance is None:
                import logging
                logger = logging.getLogger(__name__)

                # Create secret key hash for debugging (first 10 chars only)
                secret_hash = hashlib.md5(settings.jwt_secret_key.encode()).hexdigest()[:10]

                # Validate that JWT settings are properly loaded
                if not settings.jwt_secret_key or settings.jwt_secret_key == "your-secret-key-change-in-production":
                    logger.warning(f"JWT service initialized with default secret key in environment: {settings.environment}")

                logger.info(f"🔐 Creating NEW JWT service instance")
                logger.info(f"   Secret key hash: {secret_hash}")
                logger.info(f"   Secret key length: {len(settings.jwt_secret_key)} chars")
                logger.info(f"   Algorithm: {settings.jwt_algorithm}")
                logger.info(f"   Environment: {settings.environment}")

                _jwt_service_instance = JWTService()

                # Log instance creation with ID for tracking
                instance_id = id(_jwt_service_instance)
                logger.info(f"   Instance ID: {hex(instance_id)}")
            else:
                import logging
                logger = logging.getLogger(__name__)
                instance_id = id(_jwt_service_instance)
                logger.debug(f"🔄 Reusing existing JWT service instance: {hex(instance_id)}")

    return _jwt_service_instance


# Use get_jwt_service() function instead of direct jwt_service access