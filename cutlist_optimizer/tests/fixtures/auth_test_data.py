# =============================================================================
# AUTHENTICATION TEST DATA - Modify these values to change test behavior
# =============================================================================

# Test cases for login failures
LOGIN_FAILURE_CASES = [
    ('nonexistent', 'anypassword', 'Invalid username'),
    ('selloum', 'wrongpassword', 'Wrong password for valid user'),
    ('', '', 'Empty credentials'),
    ('selloum', '', 'Empty password'),
    ('', 'test', 'Empty username'),
]

# Test cases for successful logins
LOGIN_SUCCESS_CASES = [
    ('selloum', 'test', 'Mohammed Selloum'),
    ('testuser', 'test123', 'Test User'),
    ('testadmin', 'admin123', 'Test Admin'),
]

# Custom user data for testing
CUSTOM_USER_DATA = {
    'ide': 'customuser',
    'pwd': 'custompass',
    'first_name': 'Custom',
    'last_name': 'User',
    'email': 'custom@example.com',
    'has_left': False,
    'ptf_id': 1,
    'center_id': 1
} 