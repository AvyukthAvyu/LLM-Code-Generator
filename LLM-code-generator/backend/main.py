# backend/main.py
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Request, Body
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from backend.database import SessionLocal, engine
from backend import models

# load env
load_dotenv()

# try to import your existing modules
try:
    # your existing workflow that runs the agents
    from workflows.interaction import run_interaction
except Exception as e:
    run_interaction = None
    print("WARN: workflows.interaction.run_interaction NOT imported:", e)

# try to import auth + crud if present to enable token validation
auth_module = None
crud_module = None
try:
    import backend.auth as auth_module
except Exception:
    try:
        # some projects may have auth at top-level backend/auth.py
        import auth as auth_module
    except Exception:
        auth_module = None

try:
    import backend.curd as crud_module  # you listed curd.py (typo?) — try to import it
except Exception:
    try:
        import backend.crud as crud_module
    except Exception:
        crud_module = None

# Create FastAPI app
app = FastAPI(title="LLM Code Generator")

@app.on_event("startup")
def on_startup():
    # Ensure tables exist
    models.Base.metadata.create_all(bind=engine)

    # Seed admin user from env if provided
    admin_email = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if admin_email and admin_password and crud_module and hasattr(crud_module, "get_user_by_email") and hasattr(crud_module, "create_user"):
        db = SessionLocal()
        try:
            existing = crud_module.get_user_by_email(db, admin_email)
            if not existing:
                crud_module.create_user(db, email=admin_email, password=admin_password, is_admin=True)
        finally:
            db.close()

# Determine absolute frontend path (works in Docker if you copied frontend/ to /app/frontend)
PROJECT_ROOT = os.getcwd()        # when running in container your WORKDIR should be /app
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
if not os.path.isdir(FRONTEND_DIR):
    # fallback: maybe frontend is one level up
    FRONTEND_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "..", "frontend"))

if not os.path.isdir(FRONTEND_DIR):
    print("WARNING: frontend directory not found at", FRONTEND_DIR)
else:
    # mount at /frontend so API routes at root won't be overridden
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

# redirect /frontend -> /frontend/index.html for convenience
@app.get("/frontend", include_in_schema=False)
def frontend_root():
    return RedirectResponse(url="/frontend/index.html")

# serve index at root
@app.get("/", include_in_schema=False)
def root():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    # fallback JSON if file missing
    return JSONResponse({"status": "running", "message": "index.html not found"})

# Setup OAuth2 token dependency only if auth_module defines appropriate pieces
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _decode_token(token: str):
    """
    Wrapper to decode token using your auth module if available.
    Returns payload dict or raises HTTPException.
    """
    if auth_module and hasattr(auth_module, "decode_token"):
        try:
            payload = auth_module.decode_token(token)
            return payload
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")
    # no auth module available
    raise HTTPException(status_code=501, detail="Token decoding not implemented on server")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Validates token and returns user object if possible.
    Falls back to 501 if auth not implemented.
    """
    # If auth module and crud available, validate and return user object
    if auth_module and hasattr(auth_module, "decode_token") and crud_module and hasattr(crud_module, "get_user_by_email"):
        payload = _decode_token(token)
        if not payload or "sub" not in payload:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        email = payload["sub"]
        # adapt to your crud.get_user_by_email signature
        user = crud_module.get_user_by_email(db, email) if hasattr(crud_module, "get_user_by_email") else None
        # If your curd.get_user_by_email requires (db, email) you'll need to adapt this integration.
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    # If parts missing, raise 501 so caller can decide
    raise HTTPException(status_code=501, detail="Auth not configured on server")

def get_admin_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = _decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    email = payload["sub"]
    user = crud_module.get_user_by_email(db, email) if crud_module and hasattr(crud_module, "get_user_by_email") else None
    if not user:
        # Allow env-seeded admin even if DB lookup fails or user doesn't exist yet
        admin_email = os.getenv("ADMIN_USERNAME")
        if admin_email and email == admin_email:
            return {"email": email, "is_admin": True}
        raise HTTPException(status_code=401, detail="User not found")
    if not getattr(user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin only")
    return user

# if you want generate to be protected only when auth implemented set require_auth=True
REQUIRE_AUTH_FOR_GENERATE = True if auth_module and crud_module and hasattr(auth_module, "decode_token") else False

# Minimal request model for generate
class PromptRequest(BaseModel):
    prompt: str
    # optionally include metadata
    user: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str

@app.post("/auth/token")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """
    Issue an access token.
    - Primary: authenticate against DB users.
    - Fallback: ADMIN_USERNAME / ADMIN_PASSWORD env values.
    """
    if not auth_module or not hasattr(auth_module, "create_access_token"):
        raise HTTPException(status_code=501, detail="Auth not configured on server")
    # Primary: DB auth
    user = None
    if crud_module and hasattr(crud_module, "authenticate_user"):
        try:
            user = crud_module.authenticate_user(db, data.email, data.password)
        except Exception:
            user = None

    if user:
        role = "admin" if getattr(user, "is_admin", False) else "user"
        token = auth_module.create_access_token({"sub": user.email})
        return {"access_token": token, "token_type": "bearer", "role": role}

    # Fallback: env admin
    admin_email = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if admin_email and admin_password and data.email == admin_email and data.password == admin_password:
        token = auth_module.create_access_token({"sub": data.email})
        return {"access_token": token, "token_type": "bearer", "role": "admin"}

    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/auth/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """
    Create a new non-admin user.
    """
    if not crud_module or not hasattr(crud_module, "get_user_by_email") or not hasattr(crud_module, "create_user"):
        raise HTTPException(status_code=501, detail="User registration not available on server")

    existing = crud_module.get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = crud_module.create_user(db, email=data.email, password=data.password, is_admin=False)
    return {"id": user.id, "email": user.email, "is_admin": user.is_admin}

@app.get("/admin/users")
def admin_users(admin = Depends(get_admin_user), db: Session = Depends(get_db)):
    if crud_module and hasattr(crud_module, "get_all_users"):
        users = crud_module.get_all_users(db)
    else:
        users = db.query(models.User).order_by(models.User.created_at.desc()).all()
    return [
        {
            "email": u.email,
            "created_at": u.created_at.isoformat() if getattr(u, "created_at", None) else None,
            "is_admin": getattr(u, "is_admin", False),
        }
        for u in users
    ]

@app.get("/admin/chats")
def admin_chats(admin = Depends(get_admin_user), db: Session = Depends(get_db)):
    chats = db.query(models.Chat).order_by(models.Chat.created_at.desc()).all()
    rows = []
    for chat in chats:
        user = chat.owner
        last_prompt = None
        messages = sorted(chat.messages, key=lambda m: m.created_at)
        for msg in messages:
            if msg.role == "user":
                last_prompt = msg.content
            elif msg.role == "assistant":
                rows.append(
                    {
                        "username": user.email if user else None,
                        "prompt": last_prompt or "",
                        "response": msg.content,
                    }
                )
                last_prompt = None
    return rows

@app.post("/generate")
async def generate_endpoint(
    data: PromptRequest,
    request: Request,
    db: Session = Depends(get_db),
    user = Depends(get_current_user) if REQUIRE_AUTH_FOR_GENERATE else None
):
    """
    Calls your run_interaction() to generate code.
    - If your project includes auth + crud, this endpoint requires a valid token.
    - If not, it will allow unauthenticated calls (for testing).
    """
    if run_interaction is None:
        return JSONResponse({"error": "run_interaction not available on server"}, status_code=501)

    try:
        result = run_interaction(data.prompt)

        # If we have a real user and CRUD helpers, persist chat
        if user and crud_module and hasattr(crud_module, "create_chat") and hasattr(crud_module, "add_message"):
            try:
                title = (data.prompt[:60] + "...") if len(data.prompt) > 60 else data.prompt
                chat = crud_module.create_chat(db=db, user_id=user.id, title=title)
                crud_module.add_message(db=db, chat_id=chat.id, role="user", content=data.prompt)
                crud_module.add_message(db=db, chat_id=chat.id, role="assistant", content=result)
            except Exception as e:
                print("Warning: could not persist chat:", e)

        return {"response": result}
    except Exception as e:
        # log and return
        print("Error in run_interaction:", e)
        return JSONResponse({"error": str(e)}, status_code=500)

# OPTIONAL: include backend.auth router if it exports an APIRouter named `router`
if auth_module and hasattr(auth_module, "router"):
    try:
        app.include_router(auth_module.router, prefix="/auth")
        print("Included auth_module.router")
    except Exception as e:
        print("Could not include auth_module.router:", e)

# Helpful debug endpoint
@app.get("/debug")
def debug():
    info = {
        "frontend_dir": FRONTEND_DIR,
        "have_run_interaction": run_interaction is not None,
        "auth_module": bool(auth_module),
        "crud_module": bool(crud_module),
        "require_auth_for_generate": REQUIRE_AUTH_FOR_GENERATE
    }
    return info
