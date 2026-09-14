import pytest
from app.authorization import PERMISSION_MATRIX, _check_permission
from app.exceptions import AuthorizationError
from app.models.user import User

def test_permission_matrix_structure():
    assert "doctor" in PERMISSION_MATRIX
    assert "super_admin" in PERMISSION_MATRIX
    assert "nurse" in PERMISSION_MATRIX
    assert "auditor" in PERMISSION_MATRIX
    
def test_super_admin_has_all_permissions():
    user = User(email="admin@test.com", role="super_admin")
    # Should not raise AuthorizationError
    _check_permission(user, "consultation", "delete")
    _check_permission(user, "random", "action")

def test_doctor_permissions():
    user = User(email="doc@test.com", role="doctor")
    # Allowed
    _check_permission(user, "consultation", "create")
    _check_permission(user, "consultation", "update")
    
    # Denied
    with pytest.raises(AuthorizationError) as exc_info:
        _check_permission(user, "user", "create")
    assert exc_info.value.code == "INSUFFICIENT_PERMISSIONS"

def test_nurse_permissions():
    user = User(email="nurse@test.com", role="nurse")
    # Allowed
    _check_permission(user, "consultation", "create")
    _check_permission(user, "consultation", "read")
    
    # Denied
    with pytest.raises(AuthorizationError):
        _check_permission(user, "finding", "create")
        
def test_auditor_permissions():
    user = User(email="auditor@test.com", role="auditor")
    # Allowed
    _check_permission(user, "consultation", "read")
    _check_permission(user, "audit", "read")
    
    # Denied
    with pytest.raises(AuthorizationError):
        _check_permission(user, "consultation", "create")

def test_missing_role():
    user = User(email="none@test.com")
    user.role = None
    with pytest.raises(AuthorizationError) as exc_info:
        _check_permission(user, "consultation", "read")
    assert exc_info.value.code == "NO_ROLE"
