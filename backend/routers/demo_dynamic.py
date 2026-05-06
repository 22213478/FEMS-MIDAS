from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from database.connection import AsyncSessionLocal
from database.models import Job, Schedule
from scheduler.jobs import (
    acquire_job_a_execution_lock,
    pause_job_a_schedule,
    release_job_a_execution_lock,
    resume_job_a_schedule,
    run_job_a_optimization_async,
)


router = APIRouter(prefix="/api/v1/demo/dynamic-schedule", tags=["demo-dynamic-schedule"])


class DemoRunRequest(BaseModel):
    factory_id: int = Field(default=1, ge=1)
    quantity: int = Field(ge=0, le=100000)


@router.post("/run")
async def run_dynamic_schedule_demo(req: DemoRunRequest):
    """데모 전용: quantity를 업데이트하고 Job A를 즉시 1회 실행한다."""
    now = datetime.now(timezone.utc)
    latest_job_stmt = (
        select(Job)
        .where(Job.factory_id == req.factory_id)
        .order_by(Job.created_at.desc())
        .limit(1)
    )
    async with AsyncSessionLocal() as session:
        latest_job = (await session.execute(latest_job_stmt)).scalar_one_or_none()

        if latest_job is None:
            latest_job = Job(
                factory_id=req.factory_id,
                target_units="demo",
                status="pending",
                deadline_at=now + timedelta(hours=6),
                quantity=req.quantity,
                created_at=now,
            )
            session.add(latest_job)
        else:
            latest_job.quantity = req.quantity
            latest_job.deadline_at = now + timedelta(hours=6)
            latest_job.created_at = now

        await session.commit()

    acquired = await asyncio.to_thread(acquire_job_a_execution_lock, 20.0)
    if not acquired:
        raise HTTPException(status_code=409, detail="job a is currently running; retry shortly")

    pause_job_a_schedule()
    try:
        result = await run_job_a_optimization_async(dry_run=False, now=now)
        # 스케줄러 Job A와 실행 타이밍이 겹치면 asyncpg "another operation is in progress"가
        # 간헐적으로 발생할 수 있어 데모 경로에서 1회 재시도한다.
        if (result.get("db_saved") is False) and ("another operation is in progress" in str(result.get("db_error", ""))):
            await asyncio.sleep(0.6)
            result = await run_job_a_optimization_async(dry_run=False, now=datetime.now(timezone.utc))
    finally:
        resume_job_a_schedule()
        release_job_a_execution_lock()
    if result.get("db_saved") is False:
        raise HTTPException(status_code=500, detail=result.get("db_error", "job a save failed"))

    block = next(
        (b for b in result.get("schedule_blocks", []) if int(b.get("factory_id", 0)) == req.factory_id),
        None,
    )

    latest_schedule = None
    try:
        latest_schedule_stmt = (
            select(Schedule)
            .where(Schedule.factory_id == req.factory_id)
            .order_by(Schedule.created_at.desc())
            .limit(1)
        )
        async with AsyncSessionLocal() as session:
            latest_schedule = (await session.execute(latest_schedule_stmt)).scalar_one_or_none()
    except Exception:
        # 데모에서는 스케줄 재조회 실패 시에도 최적화 결과만으로 응답
        latest_schedule = None

    if block is None and latest_schedule is None:
        raise HTTPException(status_code=404, detail="no schedule generated for factory")

    return {
        "success": True,
        "message": "demo recompute completed",
        "data": {
            "factory_id": req.factory_id,
            "quantity": req.quantity,
            "inbound_source": result.get("inbound_source"),
            "recommended_temp_c": block.get("recommended_temp_c") if block else None,
            "mode": block.get("mode") if block else None,
            # 데모에서는 DB 저장값 대신 "이번 실행에서 공장에 쓴 목표 온도"를 기준으로 맞춰 보여준다.
            "schedule_target_temp_c": (
                float(block.get("recommended_temp_c", block.get("target_temp_c")))
                if block
                else float(latest_schedule.target_temp) if latest_schedule else None
            ),
            "schedule_target_temp_c_db": float(latest_schedule.target_temp) if latest_schedule else None,
            "schedule_created_at": latest_schedule.created_at.isoformat() if latest_schedule else None,
            "computed_at": result.get("computed_at"),
        },
    }
