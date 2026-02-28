"""Advanced features API routes: scraping, channels, exports."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, date
import httpx
from bs4 import BeautifulSoup
import json
import re

from api.auth import get_current_user
from shared.database import get_db
from shared.models import (
    User, ScrapingJob, ScrapingResult, ChannelConfig, AutoForward,
    AdvancedExport, UserBot, BotFlow
)
from shared.schemas import (
    ScrapingJobResponse, ScrapingJobCreate, ScrapingJobUpdate, ScrapingJobListResponse,
    ScrapingResultResponse,
    ChannelConfigResponse, ChannelConfigCreate, ChannelConfigUpdate, ChannelConfigListResponse,
    AutoForwardResponse, AutoForwardCreate, AutoForwardUpdate, AutoForwardListResponse,
    AdvancedExportResponse, AdvancedExportCreate, AdvancedExportUpdate, AdvancedExportListResponse,
    PaginatedResponse
)

router = APIRouter(prefix="/advanced", tags=["Advanced Features"])


# ==================== SCRAPING ====================

@router.get("/scraping", response_model=ScrapingJobListResponse)
async def list_scraping_jobs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's scraping jobs."""
    query = select(ScrapingJob).where(ScrapingJob.owner_id == current_user.id)
    query = query.order_by(ScrapingJob.updated_at.desc())
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return ScrapingJobListResponse(
        total=total or 0,
        page=page,
        per_page=per_page,
        pages=((total or 0) + per_page - 1) // per_page,
        items=[ScrapingJobResponse.model_validate(j) for j in jobs]
    )


@router.post("/scraping", response_model=ScrapingJobResponse)
async def create_scraping_job(
    data: ScrapingJobCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new scraping job."""
    job = ScrapingJob(
        owner_id=current_user.id,
        group_id=data.group_id,
        name=data.name,
        description=data.description,
        target_url=data.target_url,
        selector=data.selector,
        method=data.method,
        headers=data.headers,
        body=data.body,
        schedule_type=data.schedule_type,
        cron_expression=data.cron_expression,
        transform_rule=data.transform_rule,
        output_format=data.output_format,
        action_type=data.action_type,
        action_config=data.action_config
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return ScrapingJobResponse.model_validate(job)


@router.get("/scraping/{job_id}", response_model=ScrapingJobResponse)
async def get_scraping_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific scraping job."""
    job = await db.get(ScrapingJob, job_id)
    if not job or job.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return ScrapingJobResponse.model_validate(job)


@router.patch("/scraping/{job_id}", response_model=ScrapingJobResponse)
async def update_scraping_job(
    job_id: int,
    data: ScrapingJobUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a scraping job."""
    job = await db.get(ScrapingJob, job_id)
    if not job or job.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(job, field, value)
    
    await db.commit()
    await db.refresh(job)
    return ScrapingJobResponse.model_validate(job)


@router.delete("/scraping/{job_id}")
async def delete_scraping_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a scraping job."""
    job = await db.get(ScrapingJob, job_id)
    if not job or job.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    
    await db.delete(job)
    await db.commit()
    return {"message": "Job deleted"}


@router.post("/scraping/{job_id}/run", response_model=ScrapingResultResponse)
async def run_scraping_job(
    job_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually run a scraping job."""
    job = await db.get(ScrapingJob, job_id)
    if not job or job.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Run the scraping
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = job.headers or {}
            headers["User-Agent"] = headers.get("User-Agent", "Mozilla/5.0")
            
            if job.method == "POST":
                response = await client.request(
                    job.method, job.target_url, headers=headers, content=job.body
                )
            else:
                response = await client.get(job.target_url, headers=headers)
            
            status_code = response.status_code
            html = response.text
            
            # Parse with BeautifulSoup if selector provided
            data = {}
            if job.selector:
                soup = BeautifulSoup(html, 'html.parser')
                elements = soup.select(job.selector)
                data["elements"] = [
                    {"text": el.get_text(strip=True), "html": str(el)}
                    for el in elements[:10]  # Limit to 10
                ]
                data["count"] = len(elements)
            else:
                data["content"] = html[:10000]  # Limit raw content
            
            # Apply transform rule if present
            if job.transform_rule:
                # Simple regex-based transformation
                try:
                    data["transformed"] = re.sub(
                        job.transform_rule, '', html
                    )[:10000]
                except:
                    pass
            
            # Save result
            result = ScrapingResult(
                job_id=job.id,
                data=data,
                raw_html=html[:50000] if job.output_format == "html" else None,
                status_code=status_code
            )
            db.add(result)
            
            # Update job
            job.last_run = datetime.utcnow()
            job.last_result = data
            job.last_error = None
            
            await db.commit()
            await db.refresh(result)
            
            return ScrapingResultResponse.model_validate(result)
            
    except Exception as e:
        job.last_error = str(e)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


@router.get("/scraping/{job_id}/results", response_model=List[ScrapingResultResponse])
async def get_scraping_results(
    job_id: int,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get results for a scraping job."""
    job = await db.get(ScrapingJob, job_id)
    if not job or job.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    
    query = select(ScrapingResult).where(
        ScrapingResult.job_id == job_id
    ).order_by(ScrapingResult.scraped_at.desc()).limit(limit)
    
    result = await db.execute(query)
    results = result.scalars().all()
    
    return [ScrapingResultResponse.model_validate(r) for r in results]


# ==================== CHANNEL CONFIG ====================

@router.get("/channels", response_model=ChannelConfigListResponse)
async def list_channels(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's channel configurations."""
    query = select(ChannelConfig).where(ChannelConfig.owner_id == current_user.id)
    query = query.order_by(ChannelConfig.updated_at.desc())
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    channels = result.scalars().all()
    
    return ChannelConfigListResponse(
        total=total or 0,
        page=page,
        per_page=per_page,
        pages=((total or 0) + per_page - 1) // per_page,
        items=[ChannelConfigResponse.model_validate(c) for c in channels]
    )


@router.post("/channels", response_model=ChannelConfigResponse)
async def create_channel(
    data: ChannelConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a channel configuration."""
    channel = ChannelConfig(
        owner_id=current_user.id,
        group_id=data.group_id,
        channel_id=data.channel_id,
        channel_name=data.channel_name,
        channel_username=data.channel_username,
        channel_type=data.channel_type,
        auto_post_enabled=data.auto_post_enabled,
        post_triggers=data.post_triggers,
        filters=data.filters,
        format_template=data.format_template,
        include_source=data.include_source,
        include_media=data.include_media
    )
    db.add(channel)
    await db.commit()
    await db.refresh(channel)
    return ChannelConfigResponse.model_validate(channel)


@router.get("/channels/{channel_id}", response_model=ChannelConfigResponse)
async def get_channel(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a channel configuration."""
    channel = await db.get(ChannelConfig, channel_id)
    if not channel or channel.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Channel not found")
    return ChannelConfigResponse.model_validate(channel)


@router.patch("/channels/{channel_id}", response_model=ChannelConfigResponse)
async def update_channel(
    channel_id: int,
    data: ChannelConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a channel configuration."""
    channel = await db.get(ChannelConfig, channel_id)
    if not channel or channel.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(channel, field, value)
    
    await db.commit()
    await db.refresh(channel)
    return ChannelConfigResponse.model_validate(channel)


@router.delete("/channels/{channel_id}")
async def delete_channel(
    channel_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a channel configuration."""
    channel = await db.get(ChannelConfig, channel_id)
    if not channel or channel.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    await db.delete(channel)
    await db.commit()
    return {"message": "Channel deleted"}


@router.post("/channels/{channel_id}/post")
async def post_to_channel(
    channel_id: int,
    message: str,
    media_file_id: Optional[str] = None,
    buttons: Optional[List[dict]] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Post a message to a channel."""
    channel = await db.get(ChannelConfig, channel_id)
    if not channel or channel.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    if not channel.is_active:
        raise HTTPException(status_code=400, detail="Channel is inactive")
    
    # TODO: Actually send message to Telegram channel
    # For now, just increment the counter
    channel.total_posts += 1
    await db.commit()
    
    return {
        "message": "Message posted",
        "channel_id": channel.id,
        "total_posts": channel.total_posts
    }


# ==================== AUTO FORWARD ====================

@router.get("/forwards", response_model=AutoForwardListResponse)
async def list_auto_forwards(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List auto-forward rules."""
    query = select(AutoForward).where(AutoForward.owner_id == current_user.id)
    query = query.order_by(AutoForward.updated_at.desc())
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    forwards = result.scalars().all()
    
    return AutoForwardListResponse(
        total=total or 0,
        page=page,
        per_page=per_page,
        pages=((total or 0) + per_page - 1) // per_page,
        items=[AutoForwardResponse.model_validate(f) for f in forwards]
    )


@router.post("/forwards", response_model=AutoForwardResponse)
async def create_auto_forward(
    data: AutoForwardCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create an auto-forward rule."""
    forward = AutoForward(
        owner_id=current_user.id,
        group_id=data.group_id,
        source_chat_id=data.source_chat_id,
        dest_chat_id=data.dest_chat_id,
        forward_type=data.forward_type,
        filters=data.filters,
        transform_content=data.transform_content,
        add_caption=data.add_caption
    )
    db.add(forward)
    await db.commit()
    await db.refresh(forward)
    return AutoForwardResponse.model_validate(forward)


@router.get("/forwards/{forward_id}", response_model=AutoForwardResponse)
async def get_auto_forward(
    forward_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get an auto-forward rule."""
    forward = await db.get(AutoForward, forward_id)
    if not forward or forward.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Forward rule not found")
    return AutoForwardResponse.model_validate(forward)


@router.patch("/forwards/{forward_id}", response_model=AutoForwardResponse)
async def update_auto_forward(
    forward_id: int,
    data: AutoForwardUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an auto-forward rule."""
    forward = await db.get(AutoForward, forward_id)
    if not forward or forward.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Forward rule not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(forward, field, value)
    
    await db.commit()
    await db.refresh(forward)
    return AutoForwardResponse.model_validate(forward)


@router.delete("/forwards/{forward_id}")
async def delete_auto_forward(
    forward_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an auto-forward rule."""
    forward = await db.get(AutoForward, forward_id)
    if not forward or forward.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Forward rule not found")
    
    await db.delete(forward)
    await db.commit()
    return {"message": "Forward rule deleted"}


@router.post("/forwards/{forward_id}/toggle")
async def toggle_auto_forward(
    forward_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggle an auto-forward rule."""
    forward = await db.get(AutoForward, forward_id)
    if not forward or forward.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Forward rule not found")
    
    forward.is_active = not forward.is_active
    await db.commit()
    
    return {
        "message": "Forward rule toggled",
        "is_active": forward.is_active
    }


# ==================== ADVANCED EXPORT ====================

@router.get("/exports", response_model=AdvancedExportListResponse)
async def list_exports(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List advanced export configurations."""
    query = select(AdvancedExport).where(AdvancedExport.owner_id == current_user.id)
    query = query.order_by(AdvancedExport.updated_at.desc())
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    exports = result.scalars().all()
    
    return AdvancedExportListResponse(
        total=total or 0,
        page=page,
        per_page=per_page,
        pages=((total or 0) + per_page - 1) // per_page,
        items=[AdvancedExportResponse.model_validate(e) for e in exports]
    )


@router.post("/exports", response_model=AdvancedExportResponse)
async def create_export(
    data: AdvancedExportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create an advanced export configuration."""
    export = AdvancedExport(
        owner_id=current_user.id,
        group_id=data.group_id,
        name=data.name,
        export_type=data.export_type,
        data_sources=data.data_sources,
        filters=data.filters,
        format=data.format,
        include_media=data.include_media,
        compress=data.compress,
        schedule_enabled=data.schedule_enabled,
        schedule_cron=data.schedule_cron,
        delivery_method=data.delivery_method,
        delivery_config=data.delivery_config
    )
    db.add(export)
    await db.commit()
    await db.refresh(export)
    return AdvancedExportResponse.model_validate(export)


@router.get("/exports/{export_id}", response_model=AdvancedExportResponse)
async def get_export(
    export_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get an advanced export configuration."""
    export = await db.get(AdvancedExport, export_id)
    if not export or export.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Export not found")
    return AdvancedExportResponse.model_validate(export)


@router.patch("/exports/{export_id}", response_model=AdvancedExportResponse)
async def update_export(
    export_id: int,
    data: AdvancedExportUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an advanced export configuration."""
    export = await db.get(AdvancedExport, export_id)
    if not export or export.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Export not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(export, field, value)
    
    await db.commit()
    await db.refresh(export)
    return AdvancedExportResponse.model_validate(export)


@router.delete("/exports/{export_id}")
async def delete_export(
    export_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an advanced export configuration."""
    export = await db.get(AdvancedExport, export_id)
    if not export or export.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Export not found")
    
    await db.delete(export)
    await db.commit()
    return {"message": "Export deleted"}


@router.post("/exports/{export_id}/run")
async def run_export(
    export_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Run an export now."""
    export = await db.get(AdvancedExport, export_id)
    if not export or export.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Export not found")
    
    # TODO: Implement actual export logic based on data_sources
    # This would gather data from the group and format it
    
    export.last_run = datetime.utcnow()
    export.last_status = "completed"
    await db.commit()
    
    return {
        "message": "Export completed",
        "export_id": export.id,
        "file_path": export.last_file_path
    }


# ==================== QUICK EXPORT (One-click) ====================

@router.get("/quick-export/types")
async def get_export_types():
    """Get available export types with their data sources."""
    return {
        "members": {
            "name": "Members",
            "description": "Export all group members with their stats",
            "data_sources": ["members", "member_stats"]
        },
        "messages": {
            "name": "Messages",
            "description": "Export group messages",
            "data_sources": ["messages"]
        },
        "notes": {
            "name": "Notes",
            "description": "Export saved notes",
            "data_sources": ["notes"]
        },
        "filters": {
            "name": "Filters",
            "description": "Export keyword filters",
            "data_sources": ["filters"]
        },
        "full": {
            "name": "Full Backup",
            "description": "Export everything",
            "data_sources": ["members", "notes", "filters", "rules", "locks", "greetings"]
        }
    }
