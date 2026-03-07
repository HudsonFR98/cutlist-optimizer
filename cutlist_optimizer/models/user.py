import hashlib
import logging
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.declarative import declared_attr
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from cutlist_optimizer.lib.database import Base, DBSession
from cutlist_optimizer.lib import config

log = logging.getLogger(__name__)

# Association table for user-role many-to-many relationship
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)


class Role(Base):
    """Role model for permission management"""
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))

    permissions = Column(String(255), default='')
    users = relationship('User', secondary=user_roles, back_populates='roles')

    def __init__(self, name, description=None, permissions=None):
        self.name = name
        self.description = description
        self.permissions = ','.join(permissions) if permissions else ''

    def get_permissions(self) -> List[str]:
        return self.permissions.split(',') if self.permissions else []

    def has_permission(self, permission: str) -> bool:
        return permission in self.get_permissions()

    def add_permission(self, permission: str):
        permissions = self.get_permissions()
        if permission not in permissions:
            permissions.append(permission)
            self.permissions = ','.join(permissions)

    def remove_permission(self, permission: str):
        permissions = self.get_permissions()
        if permission in permissions:
            permissions.remove(permission)
            self.permissions = ','.join(permissions)


class User(Base, UserMixin):
    """User model with role-based permissions"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    ide = Column(String(50), unique=True, nullable=False)
    pwd = Column(String(128), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    email = Column(String(100))
    active = Column(Boolean, default=True)
    has_left = Column(Boolean, default=False)

    ptf_id = Column(Integer)
    center_id = Column(Integer)

    roles = relationship('Role', secondary=user_roles, back_populates='users')

    _permissions = None

    @validates('pwd')
    def _hash_password(self, key, password):
        if password and not password.startswith('pbkdf2:') and not password.startswith('sha256$'):
            return generate_password_hash(password)
        return password

    def __init__(self, ide, pwd, first_name=None, last_name=None, email=None,
                 active=True, has_left=False, ptf_id=None, center_id=None):
        self.ide = ide
        self.pwd = pwd
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.active = active
        self.has_left = has_left
        self.ptf_id = ptf_id
        self.center_id = center_id

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_id(self):
        return str(self.id)

    def is_authenticated(self):
        return self.active and not self.has_left

    def is_active(self):
        return self.active and not self.has_left

    def reload_permissions(self):
        self._permissions = set()
        for role in self.roles:
            self._permissions.update(role.get_permissions())

    def has_permission(self, permission: str) -> bool:
        if self._permissions is None:
            self.reload_permissions()
        return permission in (self._permissions or set())

    def has_role(self, role_name: str) -> bool:
        return any(role.name == role_name for role in self.roles)

    def add_role(self, role):
        if role not in self.roles:
            self.roles.append(role)
            self._permissions = None

    def remove_role(self, role):
        if role in self.roles:
            self.roles.remove(role)
            self._permissions = None

    def check_password(self, password: str) -> bool:
        if self.pwd.startswith('sha256$'):
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            if self.pwd == f'sha256${hashed_password}':
                self.pwd = generate_password_hash(password)
                DBSession.commit()
                return True
            return False
        return check_password_hash(self.pwd, password)

    @classmethod
    def authenticate(cls, username: str, password: str) -> Optional['User']:
        user = cls.query.filter_by(ide=username, active=True).first()
        if user and user.check_password(password):
            return user
        raise Exception("Invalid username or password")

    @classmethod
    def _get_initial_admin_data(cls) -> dict:
        return {
            'username': config.ADMIN_USER_USERNAME,
            'password': config.ADMIN_USER_PASSWORD,
            'first_name': config.ADMIN_USER_FIRST_NAME,
            'last_name': config.ADMIN_USER_LAST_NAME,
            'email': config.ADMIN_USER_EMAIL,
        }

    @classmethod
    def create_admin_if_not_exists(cls):
        """Ensure admin user exists and matches configured values."""
        admin_data = cls._get_initial_admin_data()

        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(
                name='admin',
                description='Administrator with all permissions',
                permissions=['admin', 'read', 'write', 'delete']
            )
            DBSession.add(admin_role)

        admin_user = cls.query.get(1)

        if not admin_user:
            admin_user = cls(
                ide=admin_data['username'],
                pwd=admin_data['password'],
                first_name=admin_data['first_name'],
                last_name=admin_data['last_name'],
                email=admin_data['email'],
                active=True,
                has_left=False,
            )
            admin_user.add_role(admin_role)
            DBSession.add(admin_user)
            DBSession.commit()
            log.info("Created admin user with username '%s'", admin_data['username'])
            return admin_user

        admin_user.ide = admin_data['username']
        admin_user.first_name = admin_data['first_name']
        admin_user.last_name = admin_data['last_name']
        admin_user.email = admin_data['email']
        admin_user.active = True
        admin_user.has_left = False
        if admin_role not in admin_user.roles:
            admin_user.add_role(admin_role)
        admin_user.pwd = admin_data['password']

        DBSession.commit()
        log.info("Updated admin user '%s' from configuration", admin_data['username'])
        return admin_user


User.query = DBSession.query_property()
Role.query = DBSession.query_property()

# For backward compatibility
Service = None
