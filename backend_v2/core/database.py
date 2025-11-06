"""Database setup and session management"""
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.pool import StaticPool

from .config import settings
from models.base import Base


class Database:
    """Database manager"""

    def __init__(self, url: str = None, echo: bool = None):
        """Initialize database"""
        self.url = url or settings.DATABASE_URL
        self.echo = echo if echo is not None else settings.DATABASE_ECHO

        # Create engine
        connect_args = {}
        if self.url.startswith('sqlite'):
            # SQLite specific settings
            connect_args = {"check_same_thread": False}
            if settings.TESTING:
                # Use in-memory database for tests
                self.engine = create_engine(
                    'sqlite:///:memory:',
                    connect_args=connect_args,
                    poolclass=StaticPool,
                    echo=self.echo
                )
            else:
                self.engine = create_engine(
                    self.url,
                    connect_args=connect_args,
                    echo=self.echo
                )
        else:
            # PostgreSQL settings
            self.engine = create_engine(
                self.url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                echo=self.echo
            )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        # Create scoped session for thread safety
        self.ScopedSession = scoped_session(self.SessionLocal)

    def create_all(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)

    def drop_all(self):
        """Drop all tables"""
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get a new session"""
        return self.SessionLocal()

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Global database instance
db = Database()


def get_db() -> Session:
    """Dependency for getting database session"""
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


def init_db():
    """Initialize database with tables"""
    db.create_all()
    print("✅ Database tables created")


def reset_db():
    """Reset database (drop and recreate all tables)"""
    db.drop_all()
    db.create_all()
    print("✅ Database reset complete")
