import logging
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database.models import Lead, ChatMessage
from services.ai_service import ai_service
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

@web_router.get("/", response_class=HTMLResponse)
async def render_landing_page(request: Request):
    """Renders B2B Responsive Landing Page."""
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

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

        # Send Telegram notification to admin
        await notify_admin_new_lead(
            lead_id=new_lead.id,
            name=new_lead.name,
            phone=new_lead.phone,
            email=new_lead.email,
            company=new_lead.company,
            message=new_lead.message
        )

        return {"success": True, "lead_id": new_lead.id, "message": "Заявка успешно создана!"}
    except Exception as e:
        logger.error(f"Error creating lead: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при сохранении заявки")

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
async def admin_dashboard(request: Request, prompt_saved: bool = False, db: AsyncSession = Depends(get_db)):
    """Renders Admin Management Dashboard."""
    leads_res = await db.execute(select(Lead).order_by(Lead.id.desc()))
    leads = leads_res.scalars().all()

    msgs_res = await db.execute(select(ChatMessage).order_by(ChatMessage.id.desc()).limit(100))
    messages = msgs_res.scalars().all()

    current_prompt = await ai_service.get_system_prompt()

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "leads": leads,
            "messages": messages,
            "current_prompt": current_prompt,
            "prompt_saved": prompt_saved
        }
    )

@web_router.post("/admin/prompt")
async def update_admin_prompt(request: Request, prompt_text: str = Form(...)):
    """Form handler for updating System Prompt in database."""
    await ai_service.update_system_prompt(prompt_text)
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "leads": [],
            "messages": [],
            "current_prompt": prompt_text,
            "prompt_saved": True
        }
    )
