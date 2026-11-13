"""Price-history and user-submission endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import SubmissionModel
from app.db.repository import get_product, load_history_points
from app.engine.history import analyze_history
from app.engine.stacker import CN_TZ
from app.schemas.api import (
    HistoryResponse,
    SubmissionCreate,
    SubmissionListResponse,
    SubmissionResponse,
)

router = APIRouter(prefix="/api", tags=["history"])

DATA_NOTE = "价格历史为演示数据，用于展示趋势分析与“先涨后降”识别。"


@router.get("/products/{product_id}/history", response_model=HistoryResponse)
def product_history(
    product_id: str,
    days: int = Query(default=90, ge=30, le=180),
    platform: str = Query(default=""),
    db: Session = Depends(get_db),
) -> HistoryResponse:
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    offers = [offer for offer in product.offers if not platform or offer.platform == platform]
    series = []
    for offer in offers:
        points = load_history_points(db, product.id, offer.platform, days)
        if not points:
            continue
        series.append(
            analyze_history(
                product_id=product.id,
                platform=offer.platform,
                platform_name=offer.platform_name,
                points=points,
                days=days,
            )
        )
    return HistoryResponse(
        product_id=product.id,
        product_title=product.title,
        days=days,
        series=series,
        data_note=DATA_NOTE,
    )


@router.post("/submissions", response_model=SubmissionResponse)
def create_submission(
    request: SubmissionCreate, db: Session = Depends(get_db)
) -> SubmissionResponse:
    product = get_product(db, request.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    row = SubmissionModel(
        product_id=request.product_id,
        platform=request.platform,
        price=request.price,
        link=request.link,
        note=request.note,
        created_at=datetime.now(CN_TZ).replace(tzinfo=None),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return SubmissionResponse(
        id=row.id,
        message="已记录你提交的价格，感谢帮助完善演示数据。",
        created_at=row.created_at,
    )


@router.get("/submissions", response_model=SubmissionListResponse)
def list_submissions(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> SubmissionListResponse:
    rows = db.scalars(
        select(SubmissionModel).order_by(SubmissionModel.id.desc()).limit(limit)
    ).all()
    return SubmissionListResponse(
        submissions=[
            SubmissionResponse(
                id=row.id,
                message=f"{row.platform} · ¥{row.price:,.0f}",
                created_at=row.created_at,
            )
            for row in rows
        ],
        total=len(rows),
    )


@router.delete("/submissions/{submission_id}")
def delete_submission(
    submission_id: int, db: Session = Depends(get_db)
) -> dict:
    row = db.get(SubmissionModel, submission_id)
    if not row:
        raise HTTPException(status_code=404, detail="提交记录不存在")
    db.delete(row)
    db.commit()
    return {"deleted": submission_id, "message": "已删除该条价格提交。"}
