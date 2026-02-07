from sqlalchemy.orm import Session
from sqlalchemy import or_
import models, schemas, auth

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, username: str = None):
    user = get_user(db, user_id)
    if user:
        if username:
            user.username = username
        db.commit()
        db.refresh(user)
    return user

def get_servers(db: Session, user_id: int):
    # Get servers the user is a member of OR owner of
    # For simplicity, we just return all servers the user is a member of
    # And we ensure owner is automatically a member
    user = get_user(db, user_id)
    return user.servers

import uuid

def create_server(db: Session, server: schemas.ServerCreate, user_id: int):
    invite_code = str(uuid.uuid4())
    db_server = models.Server(name=server.name, owner_id=user_id, invite_code=invite_code)
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    
    # Add owner as member
    user = get_user(db, user_id)
    db_server.members.append(user)
    
    # Create default "general" channel
    default_channel = models.Channel(name="general", server_id=db_server.id)
    db.add(default_channel)
    
    db.commit()
    db.refresh(db_server)
    return db_server

def get_server_channels(db: Session, server_id: int):
    return db.query(models.Channel).filter(models.Channel.server_id == server_id).all()

def create_channel(db: Session, channel: schemas.ChannelCreate, server_id: int):
    db_channel = models.Channel(**channel.dict(), server_id=server_id)
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    return db_channel

def get_channel_messages(db: Session, channel_id: int, limit: int = 50):
    return db.query(models.Message).filter(models.Message.channel_id == channel_id).order_by(models.Message.timestamp.desc()).limit(limit).all()

def create_message(db: Session, message: schemas.MessageCreate, user_id: int, channel_id: int):
    db_message = models.Message(**message.dict(), user_id=user_id, channel_id=channel_id)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def join_server(db: Session, server_id: int, user_id: int):
    server = db.query(models.Server).filter(models.Server.id == server_id).first()
    user = get_user(db, user_id)
    if server and user:
        if user not in server.members:
            server.members.append(user)
            db.commit()
    return server

def join_server_by_invite(db: Session, invite_code: str, user_id: int):
    server = db.query(models.Server).filter(models.Server.invite_code == invite_code).first()
    user = get_user(db, user_id)
    if server and user:
        if user not in server.members:
            server.members.append(user)
            db.commit()
    return server

def delete_server(db: Session, server_id: int):
    db_server = db.query(models.Server).filter(models.Server.id == server_id).first()
    if db_server:
        db.delete(db_server)
        db.commit()
    return db_server

def get_all_servers(db: Session):
    return db.query(models.Server).all()
