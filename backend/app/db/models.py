"""Database entities for business research and lead management."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

JsonType = JSON().with_variant(JSONB(), "postgresql")


def new_id() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BusinessProfile(Base):
    __tablename__ = "business_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    industry: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    products: Mapped[list] = mapped_column(JsonType, default=list, nullable=False)
    target_locations: Mapped[list] = mapped_column(JsonType, default=list, nullable=False)
    ideal_customer: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    research_runs: Mapped[list["ResearchRun"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    leads: Mapped[list["Lead"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    growth_plans: Mapped[list["GrowthPlan"]] = relationship(back_populates="business", cascade="all, delete-orphan")


class ResearchRun(Base):
    __tablename__ = "research_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    business_id: Mapped[str] = mapped_column(ForeignKey("business_profiles.id", ondelete="CASCADE"), index=True)
    run_type: Mapped[str] = mapped_column(String(40), nullable=False)
    query_params: Mapped[dict] = mapped_column(JsonType, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="pending", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    business: Mapped[BusinessProfile] = relationship(back_populates="research_runs")
    sources: Mapped[list["Source"]] = relationship(back_populates="research_run", cascade="all, delete-orphan")
    growth_plans: Mapped[list["GrowthPlan"]] = relationship(back_populates="research_run")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    research_run_id: Mapped[str] = mapped_column(ForeignKey("research_runs.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), default="web", nullable=False)
    snippet: Mapped[str] = mapped_column(Text, default="", nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    research_run: Mapped[ResearchRun] = relationship(back_populates="sources")
    lead_links: Mapped[list["LeadSource"]] = relationship(back_populates="source", cascade="all, delete-orphan")


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    business_id: Mapped[str] = mapped_column(ForeignKey("business_profiles.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    website: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(200))
    lead_type: Mapped[str] = mapped_column(String(32), default="business", nullable=False)
    fit_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    fit_reasons: Mapped[list] = mapped_column(JsonType, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="new", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    business: Mapped[BusinessProfile] = relationship(back_populates="leads")
    source_links: Mapped[list["LeadSource"]] = relationship(back_populates="lead", cascade="all, delete-orphan")


class LeadSource(Base):
    __tablename__ = "lead_sources"

    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), primary_key=True)
    relationship_type: Mapped[str] = mapped_column(String(40), default="discovered_from", nullable=False)

    lead: Mapped[Lead] = relationship(back_populates="source_links")
    source: Mapped[Source] = relationship(back_populates="lead_links")


class GrowthPlan(Base):
    __tablename__ = "growth_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    business_id: Mapped[str] = mapped_column(ForeignKey("business_profiles.id", ondelete="CASCADE"), index=True)
    research_run_id: Mapped[str | None] = mapped_column(ForeignKey("research_runs.id", ondelete="SET NULL"), nullable=True)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    recommendations: Mapped[list] = mapped_column(JsonType, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    business: Mapped[BusinessProfile] = relationship(back_populates="growth_plans")
    research_run: Mapped[ResearchRun | None] = relationship(back_populates="growth_plans")
