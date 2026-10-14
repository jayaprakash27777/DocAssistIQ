"""DocAssistIQ Backend — Application Package."""

import bcrypt
# Robust monkey-patch for passlib + bcrypt >= 4.0.0
if not hasattr(bcrypt, "__about__"):
    setattr(bcrypt, "__about__", type("about", (), {"__version__": getattr(bcrypt, "__version__", "4.0.1")}))
if not hasattr(bcrypt, "_docassistiq_patched"):
    _orig_hashpw = bcrypt.hashpw
    def _safe_hashpw(password: bytes, salt: bytes) -> bytes:
        if len(password) > 72:
            password = password[:72]
        return _orig_hashpw(password, salt)
    bcrypt.hashpw = _safe_hashpw
    bcrypt._docassistiq_patched = True
