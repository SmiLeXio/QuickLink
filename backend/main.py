from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Dict
import json

import models, schemas, crud, auth, database
from sqlalchemy import text

# Init DB and Auto Migrate
models.Base.metadata.create_all(bind=database.engine)

def check_and_migrate_db(engine):
    with engine.connect() as conn:
        try:
            # Check invite_code column in servers
            result = conn.execute(text("PRAGMA table_info(servers)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'invite_code' not in columns:
                print("Migrating database: Adding invite_code to servers table...")
                conn.execute(text("ALTER TABLE servers ADD COLUMN invite_code VARCHAR"))
                conn.execute(text("CREATE UNIQUE INDEX ix_servers_invite_code ON servers (invite_code)"))
                
                # Backfill UUIDs
                import uuid
                rows = conn.execute(text("SELECT id FROM servers")).fetchall()
                for row in rows:
                    server_id = row[0]
                    code = str(uuid.uuid4())
                    conn.execute(text("UPDATE servers SET invite_code = :code WHERE id = :id"), {"code": code, "id": server_id})
                
                conn.commit()
                print("Migration completed.")
        except Exception as e:
            print(f"Migration check failed or skipped: {e}")

check_and_migrate_db(database.engine)

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

@app.patch("/users/me", response_model=schemas.User)
def update_user_me(user_update: schemas.UserUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if user_update.username:
        # Check if username exists
        existing_user = crud.get_user_by_username(db, user_update.username)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(status_code=400, detail="Username already taken")
    return crud.update_user(db, current_user.id, username=user_update.username)

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

@app.post("/servers/join")
def join_server(
    invite_code: str = None, 
    server_id: int = None,
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    server = None
    if invite_code:
        server = crud.join_server_by_invite(db, invite_code, current_user.id)
    elif server_id:
        server = crud.join_server(db, server_id, current_user.id)
    else:
        raise HTTPException(status_code=400, detail="Either invite_code or server_id is required")
        
    if not server:
        raise HTTPException(status_code=404, detail="Server not found or invalid invite code")
    return {"status": "joined", "server": server.name}

@app.delete("/servers/{server_id}")
def delete_server(server_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    server = db.query(models.Server).filter(models.Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    if server.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    crud.delete_server(db=db, server_id=server_id)
    return {"status": "deleted"}

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

@app.get("/servers/{server_id}/members", response_model=List[schemas.User])
def read_server_members(server_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    server = db.query(models.Server).filter(models.Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    # Check if user is member
    if current_user not in server.members:
        raise HTTPException(status_code=403, detail="Not authorized")
    return server.members

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
        
        # Format message for WS using Pydantic schema to ensure correct serialization (e.g. timezone)
        # Assign sender manually to avoid extra DB query and ensure it's present
        db_message.sender = current_user
        message_schema = schemas.Message.model_validate(db_message)
        
        ws_data = {
            "type": "new_message",
            "message": json.loads(message_schema.model_dump_json())
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
