from datetime import datetime
from enum import Enum
import pytz
from flask_sqlalchemy import SQLAlchemy
from models import db

# Jakarta timezone
jakarta_tz = pytz.timezone('Asia/Jakarta')

class ModuleStatus(Enum):
    DRAFT = "Draft"
    PUBLISHED = "Published"
    ARCHIVED = "Archived"

class Module(db.Model):
    __tablename__ = 'modules'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), default='General')
    tags = db.Column(db.String(500))  # Comma-separated tags
    status = db.Column(db.Enum(ModuleStatus), default=ModuleStatus.DRAFT)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(jakarta_tz), onupdate=lambda: datetime.now(jakarta_tz))
    published_at = db.Column(db.DateTime)
    
    # Relationships
    author = db.relationship('User', backref='modules')
    
    def __repr__(self):
        return f'<Module {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'content': self.content,
            'category': self.category,
            'tags': self.tags,
            'status': self.status.name if self.status else None,
            'author_id': self.author_id,
            'author_name': self.author.name if self.author else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None
        }
    
    @property
    def tag_list(self):
        """Return tags as a list"""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    @tag_list.setter
    def tag_list(self, tag_list):
        """Set tags from a list"""
        if isinstance(tag_list, list):
            self.tags = ', '.join(tag.strip() for tag in tag_list if tag.strip())
        else:
            self.tags = tag_list