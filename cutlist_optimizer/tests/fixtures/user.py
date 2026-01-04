from cutlist_optimizer import models


# =============================================================================
# EDITABLE TEST DATA - Modify these values to change test behavior
# =============================================================================

# Test users that will be created in the database
TEST_USERS = [
    dict(
        last_name='Selloum',
        has_left=False,
        first_name='Mohammed',
        pwd='test',
        ide='selloum',
        ptf_id=3,
        email='selloum@igbmc.fr',
        center_id=1
    ),
    dict(
        last_name='Test',
        has_left=False,
        first_name='User',
        pwd='test123',
        ide='testuser',
        ptf_id=1,
        email='test@igbmc.fr',
        center_id=1
    ),
    dict(
        last_name='Test',
        has_left=False,
        first_name='Admin',
        pwd='admin123',
        ide='testadmin',
        ptf_id=1,
        email='testadmin@igbmc.fr',
        center_id=1
    ),
]

# Legacy format for backward compatibility
DATA = {
    models.User: TEST_USERS,
}