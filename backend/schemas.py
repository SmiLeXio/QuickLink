from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    
    class Config:
        from_attributes = True

# Message Schemas
class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    timestamp: datetime
    user_id: int
    channel_id: int
    sender: User

    class Config:
        from_attributes = True

# Channel Schemas
class ChannelBase(BaseModel):
    name: str

class ChannelCreate(ChannelBase):
    pass

class Channel(ChannelBase):
    id: int
    server_id: int
    
    class Config:
        from_attributes = True

# Server Schemas
class ServerBase(BaseModel):
    name: str

class ServerCreate(ServerBase):
    pass

class Server(ServerBase):
    id: int
    owner_id: int
    channels: List[Channel] = []
    
    class Config:
        from_attributes = True

class ServerWithMembers(Server):
    members: List[User] = []

# Auth
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
