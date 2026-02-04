from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Dict
import json

import models, schemas, crud, auth, database

# Init DB
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="QuickLink Discord Clone")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = auth.jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except auth.JWTError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        # user_id -> WebSocket
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def broadcast_to_server_members(self, message: dict, member_ids: List[int]):
        """Send message to all connected members of the server"""
        for uid in member_ids:
            if uid in self.active_connections:
                try:
                    await self.active_connections[uid].send_json(message)
                except:
                    # Handle broken pipe
                    pass

manager = ConnectionManager()

# --- Auth Routes ---
@app.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# --- Server/Channel Routes ---
@app.get("/servers", response_model=List[schemas.Server])
def read_servers(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.get_servers(db, user_id=current_user.id)

@app.get("/servers/all", response_model=List[schemas.Server])
def read_all_servers(db: Session = Depends(get_db)):
    return crud.get_all_servers(db)

@app.post("/servers", response_model=schemas.Server)
def create_server(server: schemas.ServerCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.create_server(db=db, server=server, user_id=current_user.id)

@app.post("/servers/{server_id}/join")
def join_server(server_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    server = crud.join_server(db, server_id, current_user.id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return {"status": "joined", "server": server.name}

@app.post("/servers/{server_id}/channels", response_model=schemas.Channel)
def create_channel(server_id: int, channel: schemas.ChannelCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Check if user is owner or member? For now let's say anyone in server can create channel or just owner
    # For simplicity: owner only
    server = db.query(models.Server).filter(models.Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    if server.owner_id != current_user.id:
         raise HTTPException(status_code=403, detail="Not authorized")
    return crud.create_channel(db=db, channel=channel, server_id=server_id)

@app.get("/servers/{server_id}/channels", response_model=List[schemas.Channel])
def read_channels(server_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.get_server_channels(db, server_id=server_id)

# --- Message Routes ---
@app.get("/channels/{channel_id}/messages", response_model=List[schemas.Message])
def read_messages(channel_id: int, limit: int = 50, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    messages = crud.get_channel_messages(db, channel_id=channel_id, limit=limit)
    # Reverse to show oldest first in chat? Or newest at bottom. 
    # Usually API returns newest first (desc), frontend reverses it.
    return messages

@app.post("/channels/{channel_id}/messages", response_model=schemas.Message)
async def create_message(channel_id: int, message: schemas.MessageCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # 1. Save to DB
    db_message = crud.create_message(db, message, user_id=current_user.id, channel_id=channel_id)
    
    # 2. Broadcast via WebSocket
    # We need to find the server this channel belongs to, then find all members
    channel = db.query(models.Channel).filter(models.Channel.id == channel_id).first()
    if channel:
        server = channel.server
        member_ids = [m.id for m in server.members]
        
        # Format message for WS
        ws_data = {
            "type": "new_message",
            "message": {
                "id": db_message.id,
                "content": db_message.content,
                "user_id": db_message.user_id,
                "channel_id": db_message.channel_id,
                "timestamp": db_message.timestamp.isoformat(),
                "sender": {"username": current_user.username}
            }
        }
        await manager.broadcast_to_server_members(ws_data, member_ids)
        
    return db_message

# --- WebSocket ---
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # We can handle direct WS messages here if needed
            # For now, we use REST API for sending messages to persist them easily
            # But we could allow sending via WS too.
            pass
    except WebSocketDisconnect:
        manager.disconnect(user_id)
