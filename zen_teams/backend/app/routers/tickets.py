"""Tickets API Router"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Agent, Company, Ticket
from app.schemas import TicketCreate, TicketResponse, TicketUpdate

router = APIRouter()


@router.post("", response_model=TicketResponse)
async def create_ticket(data: TicketCreate, db: AsyncSession = Depends(get_db)):
    # Verify company exists
    company_result = await db.execute(select(Company).where(Company.id == data.company_id))
    if not company_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Company not found")

    ticket = Ticket(**data.model_dump())
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.get("", response_model=List[TicketResponse])
async def list_tickets(company_id: UUID = None, agent_id: UUID = None, status: str = None, db: AsyncSession = Depends(get_db)):
    query = select(Ticket)
    if company_id:
        query = query.where(Ticket.company_id == company_id)
    if agent_id:
        query = query.where(Ticket.assigned_agent_id == agent_id)
    if status:
        query = query.where(Ticket.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(ticket_id: UUID, data: TicketUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(ticket, field, value)

    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.delete("/{ticket_id}")
async def delete_ticket(ticket_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    await db.delete(ticket)
    await db.commit()
    return {"message": "Ticket deleted"}


@router.post("/{ticket_id}/assign/{agent_id}")
async def assign_ticket(ticket_id: UUID, agent_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    agent_result = await db.execute(select(Agent).where(Agent.id == agent_id))
    if not agent_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Agent not found")

    ticket.assigned_agent_id = agent_id
    await db.commit()
    return {"message": f"Ticket assigned to agent {agent_id}"}
