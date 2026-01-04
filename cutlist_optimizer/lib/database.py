from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

# Create the SQLAlchemy base
Base = declarative_base()

# Create a scoped session
DBSession = scoped_session(sessionmaker())

def open(uri):
    """
    Open a connection to the database
    
    Args:
        uri (str): Database URI
    """
    engine = create_engine(uri)
    DBSession.configure(bind=engine)
    return engine