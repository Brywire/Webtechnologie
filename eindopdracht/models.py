from datetime import datetime

from flask_login import UserMixin

from extensions import db

task_dependency = db.Table(
    "task_dependency",
    db.Column(
        "prerequisite_id",
        db.Integer,
        db.ForeignKey("task.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "dependent_id",
        db.Integer,
        db.ForeignKey("task.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    tasks = db.relationship("Task", backref="owner", lazy=True)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    subject = db.Column(db.String(100), default="")
    priority = db.Column(db.String(20), default="medium")
    deadline = db.Column(db.Date, nullable=True)
    done = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    prerequisites = db.relationship(
        "Task",
        secondary=task_dependency,
        primaryjoin=(id == task_dependency.c.dependent_id),
        secondaryjoin=(id == task_dependency.c.prerequisite_id),
        backref=db.backref("dependents", lazy="select"),
    )
