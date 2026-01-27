# SQLAlchemy model for 5W1H
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import current_user
from sqlalchemy import Enum
from models import db, User
import enum

class FiveWOneHStatus(enum.Enum):
    draft = 'draft'
    open = 'open'
    closed = 'closed'

class FiveWOneH(db.Model):
    __tablename__ = 'five_w_one_h'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    who = db.Column(db.Text, nullable=False)
    what = db.Column(db.Text, nullable=False)
    when_ = db.Column('when', db.DateTime, nullable=False)
    where = db.Column(db.Text, nullable=False)
    why = db.Column(db.Text, nullable=False)
    how = db.Column(db.Text, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(Enum(FiveWOneHStatus), default=FiveWOneHStatus.draft, nullable=False)
    attachment_path = db.Column(db.String(512))
    attachments = db.Column(db.JSON, default=[])  # Store multiple attachment filenames as JSON array
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = db.relationship('User', backref='fivewoneh_entries')
