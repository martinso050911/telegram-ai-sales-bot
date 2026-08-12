import logging
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Request, Depends, HTTPException, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database.models import Lead, ChatMessage, User
from services.ai_service import ai_service
from services.auth_service import hash_password, verify_password
from services.telegram_service import notify_admin_new_lead

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

web_router = APIRouter()

class LeadCreate(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    company: Optional[str] = None
    message: Optional[str] = None

class ChatRequest(BaseModel):
    session_id: str
    message: str

# Helper Dependency for Current User
async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> Optional[User]:
    session_username = request.cookies.get("session_user")
    if not session_username:
        return None
    try:
        result = await db.execute(select(User).where(User.username == session_username))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error fetching current user: {e}")
        return None

@web_router.get("/", response_class=HTMLResponse)
async def render_landing_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Renders B2B Responsive Landing Page with user context."""
    current_user = await get_current_user(request, db)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"current_user": current_user}
    )

@web_router.get("/login", response_class=HTMLResponse)
async def render_login_page(request: Request, error: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Renders Login Page."""
    current_user = await get_current_user(request, db)
    if current_user:
        if current_user.role == "admin":
            return RedirectResponse(url="/admin", status_code=303)
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": error}
    )

@web_router.post("/login")
async def process_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Processes user login authentication and sets session cookie."""
    username = username.strip()
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "invalid_credentials"}
        )

    # Redirect based on user role
    redirect_url = "/admin" if user.role == "admin" else "/"
    response = RedirectResponse(url=redirect_url, status_code=303)
    response.set_cookie(
        key="session_user",
        value=user.username,
        httponly=True,
        max_age=86400 * 7,
        path="/"
    )
    logger.info(f"User '{user.username}' (role: {user.role}) logged in successfully.")
    return response

@web_router.get("/register", response_class=HTMLResponse)
async def render_register_page(request: Request, error: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Renders Registration Page."""
    current_user = await get_current_user(request, db)
    if current_user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"error": error}
    )

@web_router.post("/register")
async def process_register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Registers a new standard user (role: 'user')."""
    username = username.strip()
    if len(username) < 3:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "Имя пользователя должно содержать не менее 3 символов."}
        )
    if len(password) < 4:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "Пароль должен содержать минимум 4 символа."}
        )
    if password != confirm_password:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "Пароли не совпадают!"}
        )

    result = await db.execute(select(User).where(User.username == username))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "Пользователь с таким именем уже зарегистрирован."}
        )

    new_user = User(
        username=username,
        hashed_password=hash_password(password),
        role="user"
    )
    db.add(new_user)
    await db.commit()
    logger.info(f"New user '{username}' registered with role 'user'.")

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="session_user",
        value=new_user.username,
        httponly=True,
        max_age=86400 * 7,
        path="/"
    )
    return response

@web_router.get("/logout")
async def process_logout():
    """Logs out user and clears session cookie."""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="session_user", path="/")
    return response

@web_router.post("/api/leads")
async def create_lead(lead_data: LeadCreate, db: AsyncSession = Depends(get_db)):
    """Receives lead form from website, saves to database, and alerts admin via Telegram bot."""
    try:
        new_lead = Lead(
            name=lead_data.name,
            phone=lead_data.phone,
            email=lead_data.email,
            company=lead_data.company,
            message=lead_data.message,
            status="new"
        )
        db.add(new_lead)
        await db.commit()
        await db.refresh(new_lead)
    except Exception as e:
        logger.error(f"Error saving lead to database: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при сохранении заявки")

    # Send Telegram notification to admin safely in a separate try-except block
    try:
        await notify_admin_new_lead(
            lead_id=new_lead.id,
            name=new_lead.name,
            phone=new_lead.phone,
            email=new_lead.email,
            company=new_lead.company,
            message=new_lead.message
        )
    except Exception as e:
        logger.error(f"Telegram notification error caught (lead saved successfully): {e}", exc_info=True)

    return {"success": True, "lead_id": new_lead.id, "message": "Заявка успешно создана!"}


@web_router.post("/api/chat")
async def chat_with_ai(chat_req: ChatRequest):
    """Endpoint for web interactive AI sales chat widget."""
    try:
        ai_response = await ai_service.generate_response(
            session_id=chat_req.session_id,
            user_text=chat_req.message,
            source="web"
        )
        return {"response": ai_response}
    except Exception as e:
        logger.error(f"Error processing web chat message: {e}")
        raise HTTPException(status_code=500, detail="Ошибка работы AI-сервиса")

@web_router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    prompt_saved: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Renders Protected Admin Management Dashboard (role='admin' required)."""
    current_user = await get_current_user(request, db)
    if not current_user or current_user.role != "admin":
        logger.warning("Unauthorized attempt to access /admin. Redirecting to /login.")
        return RedirectResponse(url="/login?error=admin_required", status_code=303)

    leads_res = await db.execute(select(Lead).order_by(Lead.id.desc()))
    leads = leads_res.scalars().all()

    msgs_res = await db.execute(select(ChatMessage).order_by(ChatMessage.id.desc()).limit(100))
    messages = msgs_res.scalars().all()

    current_prompt = await ai_service.get_system_prompt()

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "current_user": current_user,
            "leads": leads,
            "messages": messages,
            "current_prompt": current_prompt,
            "prompt_saved": prompt_saved
        }
    )

@web_router.post("/admin/prompt")
async def update_admin_prompt(
    request: Request,
    prompt_text: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Form handler for updating System Prompt in database (role='admin' required)."""
    current_user = await get_current_user(request, db)
    if not current_user or current_user.role != "admin":
        return RedirectResponse(url="/login?error=admin_required", status_code=303)

    await ai_service.update_system_prompt(prompt_text)

    leads_res = await db.execute(select(Lead).order_by(Lead.id.desc()))
    leads = leads_res.scalars().all()

    msgs_res = await db.execute(select(ChatMessage).order_by(ChatMessage.id.desc()).limit(100))
    messages = msgs_res.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "current_user": current_user,
            "leads": leads,
            "messages": messages,
            "current_prompt": prompt_text,
            "prompt_saved": True
        }
    )

@web_router.post("/admin/status/{lead_id}")
async def update_lead_status(
    lead_id: int,
    request: Request,
    new_status: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Updates status of a lead (role='admin' required)."""
    current_user = await get_current_user(request, db)
    if not current_user or current_user.role != "admin":
        return RedirectResponse(url="/login?error=admin_required", status_code=303)

    lead_res = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = lead_res.scalar_one_or_none()
    if lead:
        lead.status = new_status
        await db.commit()
        logger.info(f"Lead #{lead_id} status updated to '{new_status}' by admin '{current_user.username}'.")
    return RedirectResponse(url="/admin#leads-section", status_code=303)

@web_router.post("/admin/delete/{lead_id}")
async def delete_lead(
    lead_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Deletes a lead from the database (role='admin' required)."""
    current_user = await get_current_user(request, db)
    if not current_user or current_user.role != "admin":
        return RedirectResponse(url="/login?error=admin_required", status_code=303)

    lead_res = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = lead_res.scalar_one_or_none()
    if lead:
        await db.delete(lead)
        await db.commit()
        logger.info(f"Lead #{lead_id} deleted by admin '{current_user.username}'.")
    return RedirectResponse(url="/admin#leads-section", status_code=303)

