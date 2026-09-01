from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Optional, Union

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_provider_staff
from app.api.pagination import CommonQuery, paginate
from app.db.session import get_db
from app.models.application import Application
from app.models.beneficiary import Beneficiary
from app.models.enums import ApplicationStatus, BeneficiaryStatus, OutcomeStage, UserRole
from app.models.outcome import Outcome
from app.models.training import TrainingProgram
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationOut,
    ApplicationUpdate,
    CertificateIssue,
)
from app.schemas.common import Page
from app.schemas.mobile import MobileApplicationOut, MobileApplicationRequest
from app.services import audit
from app.services.eligibility import check_eligibility

router = APIRouter(prefix="/applications", tags=["applications"])

_ENROLLED_STATES = {
    ApplicationStatus.ENROLLED,
    ApplicationStatus.IN_PROGRESS,
    ApplicationStatus.COMPLETED,
    ApplicationStatus.CERTIFIED,
}


def _now():
    return datetime.now(timezone.utc)


@router.get("", response_model=Page[ApplicationOut])
def list_applications(
    common: CommonQuery = Depends(),
    beneficiary_id: Optional[str] = None,
    program_id: Optional[str] = None,
    status_: Optional[ApplicationStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Application)
    if beneficiary_id:
        stmt = stmt.where(Application.beneficiary_id == beneficiary_id)
    if program_id:
        stmt = stmt.where(Application.program_id == program_id)
    if status_:
        stmt = stmt.where(Application.status == status_)
    items, total = paginate(db, stmt, common, Application)
    return Page.build([ApplicationOut.model_validate(i) for i in items], total, common.page, common.page_size)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    # Two request shapes share this path — see the docstring. Schema only.
    response_model=None,
    responses={201: {"model": Union[ApplicationOut, MobileApplicationOut]}},
)
def create_application(
    body: dict = Body(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """Apply to a training programme — one path, two clients.

    The Android app posts `{beneficiaryId, skillId, trainingId}` for itself; the
    dashboard posts an `ApplicationCreate` on a beneficiary's behalf, which stays
    staff-only. `trainingId` is what tells them apart.
    """
    if "trainingId" in body or "training_id" in body:
        from app.api.routes.mobile import mobile_submit_application

        return mobile_submit_application(MobileApplicationRequest.model_validate(body), db, user)

    if user.role not in (UserRole.ADMIN, UserRole.GOV_OFFICER):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Requires one of roles: admin, gov_officer")
    payload = ApplicationCreate.model_validate(body)
    beneficiary = db.get(Beneficiary, payload.beneficiary_id)
    program = db.get(TrainingProgram, payload.program_id)
    if not beneficiary or not program:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Beneficiary or program not found")

    dup = db.execute(
        select(Application).where(
            Application.beneficiary_id == beneficiary.id,
            Application.program_id == program.id,
            Application.status.notin_([ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN]),
        )
    ).scalar_one_or_none()
    if dup:
        raise HTTPException(status.HTTP_409_CONFLICT, "An active application already exists for this program")

    report = check_eligibility(beneficiary, program)
    app_row = Application(
        beneficiary_id=beneficiary.id,
        program_id=program.id,
        recommendation_id=payload.recommendation_id,
        status=ApplicationStatus.SUBMITTED,
        eligibility_passed=report["passed"],
        eligibility_report=report,
        submitted_at=_now(),
        notes=payload.notes,
        is_demo=beneficiary.is_demo,
    )
    db.add(app_row)
    db.commit()
    db.refresh(app_row)
    db.add(Outcome(beneficiary_id=beneficiary.id, application_id=app_row.id, stage=OutcomeStage.RECOMMENDATION, occurred_on=_now().date(), is_demo=beneficiary.is_demo, details={"event": "applied", "program": program.title}))
    db.commit()
    audit.record(db, action="application.create", actor=user, entity_type="application", entity_id=app_row.id)
    return ApplicationOut.model_validate(app_row)


@router.get("/{application_id}", response_model=ApplicationOut)
def get_application(application_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = db.get(Application, application_id)
    if not a:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")
    return ApplicationOut.model_validate(a)


@router.patch("/{application_id}", response_model=ApplicationOut)
def update_application(application_id: str, payload: ApplicationUpdate, db: Session = Depends(get_db), user: User = Depends(require_provider_staff)):
    a = db.get(Application, application_id)
    if not a:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")

    prev_status = a.status
    data = payload.model_dump(exclude_unset=True)
    new_status: Optional[ApplicationStatus] = data.pop("status", None)
    for f, v in data.items():
        setattr(a, f, v)

    if new_status and new_status != prev_status:
        _transition(db, a, new_status)

    db.commit()
    db.refresh(a)
    audit.record(db, action="application.update", actor=user, entity_type="application", entity_id=a.id, changes={"from": prev_status.value, "to": a.status.value})
    return ApplicationOut.model_validate(a)


def _transition(db: Session, a: Application, new_status: ApplicationStatus) -> None:
    program = a.program
    beneficiary = a.beneficiary
    a.status = new_status

    if new_status == ApplicationStatus.ACCEPTED:
        a.decided_at = _now()
    elif new_status == ApplicationStatus.ENROLLED:
        a.enrolled_at = _now()
        program.filled_seats = min(program.total_seats, program.filled_seats + 1)
        beneficiary.status = BeneficiaryStatus.IN_TRAINING
        db.add(Outcome(beneficiary_id=beneficiary.id, application_id=a.id, stage=OutcomeStage.TRAINING, occurred_on=_now().date(), is_demo=beneficiary.is_demo, details={"event": "enrolled", "program": program.title}))
    elif new_status == ApplicationStatus.COMPLETED:
        a.completed_at = _now()
        a.progress_pct = 100.0
    elif new_status == ApplicationStatus.CERTIFIED:
        beneficiary.status = BeneficiaryStatus.CERTIFIED
        if not a.certificate_number:
            a.certificate_number = f"KAI-{program.certification_body or 'SSC'}-{secrets.token_hex(4).upper()}"
        db.add(Outcome(beneficiary_id=beneficiary.id, application_id=a.id, stage=OutcomeStage.CERTIFICATION, occurred_on=_now().date(), is_demo=beneficiary.is_demo, details={"event": "certified", "certificate": a.certificate_number}))
    elif new_status in (ApplicationStatus.WITHDRAWN, ApplicationStatus.REJECTED):
        if a.enrolled_at and program.filled_seats > 0:
            program.filled_seats -= 1


@router.post("/{application_id}/enroll", response_model=ApplicationOut)
def enroll(application_id: str, db: Session = Depends(get_db), user: User = Depends(require_provider_staff)):
    a = db.get(Application, application_id)
    if not a:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")
    if not a.eligibility_passed:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Applicant did not pass eligibility checks")
    if a.program.seats_available <= 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "No seats available")
    _transition(db, a, ApplicationStatus.ENROLLED)
    db.commit()
    db.refresh(a)
    audit.record(db, action="application.enroll", actor=user, entity_type="application", entity_id=a.id)
    return ApplicationOut.model_validate(a)


@router.post("/{application_id}/certificate", response_model=ApplicationOut)
def issue_certificate(application_id: str, payload: CertificateIssue, db: Session = Depends(get_db), user: User = Depends(require_provider_staff)):
    a = db.get(Application, application_id)
    if not a:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")
    if a.status not in _ENROLLED_STATES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Applicant is not enrolled")
    a.assessment_score = payload.assessment_score
    a.certificate_number = payload.certificate_number or a.certificate_number
    passed = payload.assessment_score >= 50
    _transition(db, a, ApplicationStatus.CERTIFIED if passed else ApplicationStatus.COMPLETED)
    a.certificate_url = f"/certificates/{a.certificate_number}.pdf" if passed else None
    db.commit()
    db.refresh(a)
    audit.record(db, action="application.certificate", actor=user, entity_type="application", entity_id=a.id, changes={"score": payload.assessment_score, "passed": passed})
    return ApplicationOut.model_validate(a)
