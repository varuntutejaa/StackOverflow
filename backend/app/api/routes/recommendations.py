from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_staff
from app.api.pagination import CommonQuery, paginate
from app.db.session import get_db
from app.models.beneficiary import Beneficiary
from app.models.enums import BeneficiaryStatus
from app.models.recommendation import Recommendation
from app.models.user import User
from app.schemas.common import Page
from app.schemas.recommendation import (
    AcceptRecommendationRequest,
    GenerateRecommendationsRequest,
    RecommendationOut,
    RecommendationResult,
    WeightsOut,
)
from app.services import audit
from app.services.recommendation_engine import (
    ENGINE_VERSION,
    WEIGHT_DESCRIPTIONS,
    RecommendationEngine,
    build_recommendation_payloads,
    load_weights,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/weights", response_model=WeightsOut)
def get_weights(user: User = Depends(get_current_user)):
    return WeightsOut(weights=load_weights(), description=WEIGHT_DESCRIPTIONS)


@router.get("", response_model=Page[RecommendationOut])
def list_recommendations(
    common: CommonQuery = Depends(),
    beneficiary_id: Optional[str] = None,
    min_score: Optional[float] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Recommendation)
    if beneficiary_id:
        stmt = stmt.where(Recommendation.beneficiary_id == beneficiary_id)
    if min_score is not None:
        stmt = stmt.where(Recommendation.match_score >= min_score)
    items, total = paginate(db, stmt, common, Recommendation, sortable={"match_score": Recommendation.match_score, "rank": Recommendation.rank})
    return Page.build([RecommendationOut.model_validate(i) for i in items], total, common.page, common.page_size)


@router.post("/generate", response_model=RecommendationResult)
def generate(payload: GenerateRecommendationsRequest, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    beneficiary = db.get(Beneficiary, payload.beneficiary_id)
    if not beneficiary:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Beneficiary not found")

    weights = load_weights(payload.weights_override)
    engine = RecommendationEngine(db, weights=weights)
    results = engine.recommend(beneficiary, top_n=payload.top_n)

    latest_interview = beneficiary.interviews[-1].id if beneficiary.interviews else None
    stored: list[Recommendation] = []
    if payload.persist:
        db.query(Recommendation).filter(
            Recommendation.beneficiary_id == beneficiary.id,
            Recommendation.is_accepted.is_(None),
        ).delete(synchronize_session=False)
        for data in build_recommendation_payloads(results, beneficiary.id, latest_interview, beneficiary.is_demo, weights):
            rec = Recommendation(**data)
            db.add(rec)
            stored.append(rec)
        if beneficiary.status in (BeneficiaryStatus.INTERVIEW_DONE, BeneficiaryStatus.INTERVIEW_PENDING, BeneficiaryStatus.REGISTERED):
            beneficiary.status = BeneficiaryStatus.RECOMMENDED
        db.commit()
        for rec in stored:
            db.refresh(rec)
        audit.record(db, action="recommendation.generate", actor=user, entity_type="beneficiary", entity_id=beneficiary.id, changes={"count": len(stored), "weights": weights})
        out = [RecommendationOut.model_validate(r) for r in stored]
    else:
        out = [
            RecommendationOut(
                id="preview",
                beneficiary_id=beneficiary.id,
                rank=r["rank"],
                match_score=r["match_score"],
                factor_scores=r["factor_scores"],
                reasons=r["reasons"],
                skill_gaps=r["skill_gaps"],
                career_pathway=r["career_pathway"],
                engine_version=ENGINE_VERSION,
                is_demo=beneficiary.is_demo,
                created_at=datetime.now(timezone.utc),
            )
            for r in results
        ]

    return RecommendationResult(
        beneficiary_id=beneficiary.id,
        engine_version=ENGINE_VERSION,
        weights=weights,
        generated_at=datetime.now(timezone.utc),
        recommendations=out,
    )


@router.get("/{recommendation_id}", response_model=RecommendationOut)
def get_recommendation(recommendation_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = db.get(Recommendation, recommendation_id)
    if not rec:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recommendation not found")
    return RecommendationOut.model_validate(rec)


@router.post("/{recommendation_id}/decision", response_model=RecommendationOut)
def decide(recommendation_id: str, payload: AcceptRecommendationRequest, db: Session = Depends(get_db), user: User = Depends(require_staff)):
    rec = db.get(Recommendation, recommendation_id)
    if not rec:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recommendation not found")
    rec.is_accepted = payload.accepted
    db.commit()
    db.refresh(rec)
    audit.record(db, action="recommendation.decision", actor=user, entity_type="recommendation", entity_id=rec.id, changes={"accepted": payload.accepted})
    return RecommendationOut.model_validate(rec)
