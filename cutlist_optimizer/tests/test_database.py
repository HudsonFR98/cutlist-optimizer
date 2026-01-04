import pytest
from sqlalchemy import text
from cutlist_optimizer.lib import database
from cutlist_optimizer.lib import config


def test_database_connection():
    """
    Test that the application can successfully connect to the database.
    
    This is a fundamental test that verifies the database connection
    is working properly. It's essential because if the database connection
    fails, most other functionality in the application will not work.
    
    The test:
    1. Opens a database connection using the test configuration
    2. Executes a simple SQL query (SELECT 1) to verify connectivity
    3. Verifies the query returns the expected result
    4. Cleans up the database session
    
    This test should run first in the test suite as it's a prerequisite
    for other database-dependent tests.
    
    Assertions:
        - Database connection should be established successfully
        - Simple query should execute and return expected result (1)
    """
    try:
        # Step 1: Open database connection using test configuration
        database.open(config.SQLALCHEMY_DATABASE_URI)
        # Step 2: Execute a simple test query to verify connectivity
        result = database.DBSession.execute(text("SELECT 1"))
        # Step 3: Verify the query returned the expected result
        assert result.scalar() == 1
    finally:
        # Step 4: Clean up database session
        database.DBSession.remove()