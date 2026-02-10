from sqlalchemy.orm import Session
from . import models
from .auth import get_password_hash, verify_password

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, email: str, password: str, is_admin=False):
    hashed = get_password_hash(password)
    user = models.User(email=email, hashed_password=hashed, is_admin=is_admin)
    db.add(user); db.commit(); db.refresh(user)
    return user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user: return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_chat(db: Session, user_id: int, title: str):
    chat = models.Chat(user_id=user_id, title=title)
    db.add(chat); db.commit(); db.refresh(chat)
    return chat

def get_chats_for_user(db: Session, user_id: int):
    return db.query(models.Chat).filter(models.Chat.user_id == user_id).order_by(models.Chat.created_at.desc()).all()

def get_chat(db: Session, chat_id: int, user_id: int = None):
    q = db.query(models.Chat).filter(models.Chat.id == chat_id)
    if user_id:
        q = q.filter(models.Chat.user_id == user_id)
    return q.first()

def add_message(db: Session, chat_id: int, role: str, content: str):
    msg = models.Message(chat_id=chat_id, role=role, content=content)
    db.add(msg); db.commit(); db.refresh(msg)
    return msg

def get_messages(db: Session, chat_id: int):
    return db.query(models.Message).filter(models.Message.chat_id == chat_id).order_by(models.Message.created_at).all()

# Admin helpers
def get_all_users(db: Session, limit: int = 100):
    return db.query(models.User).order_by(models.User.created_at.desc()).limit(limit).all()

def get_user_count(db: Session):
    return db.query(models.User).count()
