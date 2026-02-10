from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from .models import SignupRequest
from .hash_utils import hash_password, verify_password
from .jwt_utils import create_access_token, verify_token
from config.db import users_collection

router = APIRouter()
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthCredentials = Depends(security)):
    """Dependency to extract and verify JWT token from request"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return {"username": user["username"], "role": user["role"]}


@router.post("/signup")
def signup(req: SignupRequest):
    """Register a new user"""
    if users_collection.find_one({"username": req.username}):
        raise HTTPException(status_code=400, detail="User already exists")
    
    users_collection.insert_one({
        "username": req.username,
        "password": hash_password(req.password),
        "role": req.role
    })
    return {"message": "User created successfully", "username": req.username}


@router.post("/login")
def login(username: str, password: str):
    """Login and get JWT token"""
    user = users_collection.find_one({"username": username})
    
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Create JWT token
    access_token = create_access_token(data={"sub": username})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": username,
        "role": user["role"]
    }


@router.get("/me")
def get_current_user_info(user=Depends(get_current_user)):
    """Get current authenticated user info"""
    return user

    