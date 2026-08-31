"""Idempotent seed / demo-data builder.

Usage:
    python -m app.seed.seed              # create schema (sqlite) + seed if empty
    python -m app.seed.seed --fresh      # DROP ALL tables, recreate, seed
    python -m app.seed.seed --demo-only  # (re)build only the Ramesh Kumar demo
"""
from __future__ import annotations

import argparse
import random
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

import app.models  # noqa: F401  (register mappers)
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.application import Application
from app.models.beneficiary import Beneficiary
from app.models.enums import (
    ApplicationStatus,
    BeneficiaryStatus,
    EducationLevel,
    EmploymentPreference,
    Gender,
    InterviewStatus,
    Language,
    Mobility,
    NotificationType,
    OutcomeStage,
    OutcomeType,
    TrainingStatus,
    UserRole,
)
from app.models.interview import Interview
from app.models.location import Location
from app.models.notification import Notification
from app.models.opportunity import Opportunity, SkillDemand
from app.models.outcome import Outcome
from app.models.recommendation import Recommendation
from app.models.skill import NsqfRole, Skill
from app.models.training import TrainingProgram, TrainingProvider
from app.models.user import User
from app.seed import data as D
from app.services import interview_runner
from app.services.recommendation_engine import (
    RecommendationEngine,
    build_recommendation_payloads,
    load_weights,
)

configure_logging()
log = get_logger("seed")
random.seed(26097)

FIRST_NAMES_M = ["Ramesh", "Suresh", "Dinesh", "Mahesh", "Rajesh", "Vikas", "Sanjay", "Amit", "Deepak", "Manoj", "Arjun", "Rohit", "Pankaj", "Santosh"]
FIRST_NAMES_F = ["Sunita", "Anita", "Kavita", "Rekha", "Pooja", "Sita", "Gita", "Lakshmi", "Radha", "Meena", "Sarita", "Asha", "Kiran", "Nirmala"]
SURNAMES = ["Kumar", "Das", "Ram", "Baraik", "Mahli", "Lohra", "Tirkey", "Bhagat", "Turi", "Paswan", "Rajwar", "Ravidas"]
OCCUPATIONS = ["agriculture", "daily wage labour", "unemployed", "construction", "domestic work", "weaver", "student", "shopkeeper"]
SKILL_POOL = ["farming", "tailoring", "masonry", "driving", "electrical", "computer", "poultry", "handloom", "welding", "beautician"]
INTEREST_POOL = ["solar", "electronics", "beautician", "auto", "computer", "dairy", "food processing", "tailoring", "welding", "retail", "healthcare"]
CONSTRAINT_POOL = ["financial", "family responsibility", "distance", "time", "childcare", "health"]


def _reset_schema():
    log.warning("dropping_all_tables")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _ensure_schema():
    Base.metadata.create_all(bind=engine)


def _seed_users(db):
    users = {}
    defs = [
        (settings.seed_admin_email, "KaushAI Administrator", UserRole.ADMIN, settings.seed_admin_password, "Ministry of Social Justice & Empowerment", None),
        ("officer@kaushai.gov.in", "Priya Sharma (Dist. Welfare Officer)", UserRole.GOV_OFFICER, "Officer@2026", "Dept. of SC/ST Welfare, Jharkhand", "Ranchi"),
        ("provider@kaushai.gov.in", "Tata STRIVE Coordinator", UserRole.TRAINING_PROVIDER, "Provider@2026", "Tata STRIVE Skill Centre Jamshedpur", "East Singhbhum"),
        ("ramesh@kaushai.gov.in", "Ramesh Kumar", UserRole.BENEFICIARY, "Ramesh@2026", None, "Ranchi"),
    ]
    for email, name, role, pw, org, district in defs:
        u = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if not u:
            u = User(email=email, full_name=name, role=role, organisation=org, district=district,
                     hashed_password=hash_password(pw), is_active=True, is_email_verified=True)
            db.add(u)
        users[role.value if role != UserRole.BENEFICIARY else "beneficiary_user"] = u
    db.flush()
    return users


def _seed_locations(db):
    locs = {}
    for state, district, block, lat, lng, pop, sc, lit, lgd in D.LOCATIONS:
        loc = db.execute(select(Location).where(Location.district == district)).scalar_one_or_none()
        if not loc:
            loc = Location(state=state, district=district, block=block, latitude=lat, longitude=lng,
                           population=pop, sc_population=sc, literacy_rate=lit, lgd_code=lgd)
            db.add(loc)
        locs[district] = loc
    db.flush()
    return locs


def _seed_skills(db):
    skills = {}
    for row in D.SKILLS:
        (name, code, sector, nsqf, min_edu, min_age, max_age, hours, wage, self_emp, tags, prereqs, demand) = row
        s = db.execute(select(Skill).where(Skill.name == name)).scalar_one_or_none()
        if not s:
            s = Skill(name=name, code=code, sector=sector, nsqf_level=nsqf, min_education=min_edu,
                      min_age=min_age, max_age=max_age, typical_duration_hours=hours, avg_wage_monthly=wage,
                      self_employable=self_emp, tags=tags, prerequisites=prereqs, demand_index=demand,
                      description=f"NSQF Level {nsqf} skill in {sector}. QP ref {code}. (DEMO/SIMULATED catalogue entry.)",
                      is_simulated=True)
            db.add(s)
        skills[name] = s
    db.flush()
    return skills


def _seed_roles(db, skills):
    roles = {}
    for (title, nco, qp, sector, nsqf, elig, wage, outlook, sep) in D.NSQF_ROLES:
        r = db.execute(select(NsqfRole).where(NsqfRole.title == title)).scalar_one_or_none()
        if not r:
            r = NsqfRole(title=title, nco_code=nco, qp_code=qp, sector=sector, nsqf_level=nsqf,
                         eligibility=elig, entry_wage_monthly=wage, growth_outlook=outlook,
                         self_employment_path=sep, is_simulated=True,
                         description=f"{title} — NCO {nco}, aligned to QP {qp}. (DEMO/SIMULATED.)")
            # link skills sharing the QP code or sector
            linked = [s for s in skills.values() if s.code == qp or s.sector == sector]
            r.skills = linked[:4]
            db.add(r)
        roles[title] = r
    db.flush()
    return roles


def _seed_providers(db, locs):
    providers = []
    districts = list(locs.keys())
    for i, (name, ptype, accr, rating, email, phone) in enumerate(D.PROVIDERS):
        p = db.execute(select(TrainingProvider).where(TrainingProvider.name == name)).scalar_one_or_none()
        if not p:
            loc = locs[districts[i % len(districts)]]
            p = TrainingProvider(name=name, type=ptype, accreditation=accr, rating=rating,
                                 contact_email=email, contact_phone=phone, location_id=loc.id,
                                 address=f"{name}, {loc.district}, Jharkhand", is_simulated=True)
            db.add(p)
        providers.append(p)
    db.flush()
    return providers


def _seed_programs(db, skills, providers, locs):
    programs = []
    districts = list(locs.values())
    today = date.today()
    for idx, skill in enumerate(skills.values()):
        for batch in range(2):
            provider = providers[(idx + batch) % len(providers)]
            loc = districts[(idx * 2 + batch) % len(districts)]
            title = f"{skill.name} — Batch {today.year}-{idx}{batch}"
            existing = db.execute(select(TrainingProgram).where(TrainingProgram.title == title)).scalar_one_or_none()
            if existing:
                programs.append(existing)
                continue
            start = today + timedelta(days=random.choice([-30, -10, 15, 40, 75]))
            weeks = max(4, skill.typical_duration_hours // 25)
            status = TrainingStatus.ONGOING if start <= today <= start + timedelta(weeks=weeks) else (
                TrainingStatus.OPEN if start > today else TrainingStatus.COMPLETED)
            total = random.choice([25, 30, 40])
            p = TrainingProgram(
                title=title, provider_id=provider.id, skill_id=skill.id, nsqf_level=skill.nsqf_level,
                mode=random.choice(["offline", "offline", "blended"]),
                duration_hours=skill.typical_duration_hours, duration_weeks=weeks,
                total_seats=total, filled_seats=random.randint(0, total - 5),
                fee=0, stipend_monthly=random.choice([0, 1000, 1500]),
                is_residential=random.random() < 0.2, location_id=loc.id,
                start_date=start, end_date=start + timedelta(weeks=weeks),
                application_deadline=start - timedelta(days=7),
                eligibility_min_education=skill.min_education, eligibility_min_age=skill.min_age,
                eligibility_max_age=skill.max_age or 45,
                eligibility_notes=["SC category under PM-AJAY", "Aadhaar + bank account", "Domicile of Jharkhand"],
                status=status, certification_body=skill.code.split("/")[0] + " SSC", is_simulated=True,
            )
            db.add(p)
            programs.append(p)
    db.flush()
    return programs


def _seed_skill_demand(db, skills, locs):
    skill_list = list(skills.values())
    period = "2026-Q1"
    for loc in locs.values():
        sample = random.sample(skill_list, k=random.randint(8, 14))
        for s in sample:
            exists = db.execute(
                select(SkillDemand).where(SkillDemand.location_id == loc.id, SkillDemand.skill_id == s.id)
            ).scalar_one_or_none()
            if exists:
                continue
            demand = min(100, max(10, s.demand_index + random.randint(-18, 18)))
            supply = max(5, demand - random.randint(5, 45))
            db.add(SkillDemand(
                location_id=loc.id, skill_id=s.id, demand_score=demand, supply_score=supply,
                open_positions=random.randint(5, 120), trained_workforce=random.randint(10, 200),
                active_beneficiaries=random.randint(0, 40), period=period, is_simulated=True,
            ))
    db.flush()


def _seed_opportunities(db, skills, roles, locs):
    skill_list = list(skills.values())
    employers = ["Adani Solar EPC", "Tata Power DDL vendor", "L&T Construction", "Local Kirana Federation",
                 "Jharkhand Milk Federation (Medha)", "Vedanta ESL Steel", "District Hospital", "Rooftop Solar Co-op",
                 "SHG Cluster Enterprise", "Maruti Service Partner"]
    for loc in locs.values():
        for _ in range(random.randint(2, 5)):
            s = random.choice(skill_list)
            kind = "self_employment" if (s.self_employable and random.random() < 0.4) else "wage_job"
            db.add(Opportunity(
                title=f"{s.name} opening — {loc.district}",
                kind=kind, sector=s.sector, location_id=loc.id, skill_id=s.id,
                employer=random.choice(employers) if kind == "wage_job" else None,
                openings=random.randint(1, 25),
                wage_monthly_min=(s.avg_wage_monthly or 10000) - 1500,
                wage_monthly_max=(s.avg_wage_monthly or 10000) + 3500,
                source="simulated-district-employment-cell",
                valid_till=date.today() + timedelta(days=random.randint(20, 120)),
                description=f"(DEMO/SIMULATED) Local {kind.replace('_', ' ')} demand for {s.name} in {loc.district}.",
                is_active=True, is_simulated=True,
            ))
    db.flush()


def _random_beneficiary(db, locs, officer, i):
    female = random.random() < 0.5
    name = f"{random.choice(FIRST_NAMES_F if female else FIRST_NAMES_M)} {random.choice(SURNAMES)}"
    loc = random.choice(list(locs.values()))
    edu = random.choice([EducationLevel.NONE, EducationLevel.PRIMARY, EducationLevel.MIDDLE,
                         EducationLevel.SECONDARY, EducationLevel.SECONDARY, EducationLevel.SENIOR_SECONDARY,
                         EducationLevel.ITI])
    b = Beneficiary(
        full_name=name, age=random.randint(18, 40),
        gender=Gender.FEMALE if female else Gender.MALE,
        phone=f"9{random.randint(100000000, 999999999)}",
        preferred_language=random.choice([Language.HINDI, Language.HINDI, Language.SANTHALI, Language.HO, Language.MUNDARI]),
        social_category="SC", pmajay_id=f"PMAJAY-JH-{loc.district[:3].upper()}-{1000 + i}",
        location_id=loc.id, village=f"{random.choice(['Bara', 'Chota', 'Naya', 'Purana'])}{random.choice(['tola', 'gaon', 'pur'])}",
        education_level=edu, current_occupation=random.choice(OCCUPATIONS),
        family_occupation=random.choice(OCCUPATIONS), monthly_income=random.choice([0, 2000, 3500, 5000, 6500]),
        skills=random.sample(SKILL_POOL, k=random.randint(0, 3)),
        interests=random.sample(INTEREST_POOL, k=random.randint(1, 3)),
        constraints=random.sample(CONSTRAINT_POOL, k=random.randint(0, 2)),
        mobility=random.choice([Mobility.LOCAL, Mobility.LOCAL, Mobility.DISTRICT, Mobility.STATE]),
        employment_preference=random.choice([EmploymentPreference.WAGE_EMPLOYMENT, EmploymentPreference.SELF_EMPLOYMENT, EmploymentPreference.ANY]),
        has_smartphone=random.random() < 0.55, has_bank_account=random.random() < 0.9,
        status=BeneficiaryStatus.INTERVIEW_PENDING, created_by_id=officer.id, is_demo=True,
    )
    db.add(b)
    return b


def _progress_beneficiary(db, b, skills, programs, weights):
    """Push a subset of beneficiaries through the pipeline for realistic dashboards."""
    roll = random.random()
    if roll < 0.25:
        return  # stays at interview_pending

    # simulated completed interview
    iv = Interview(beneficiary_id=b.id, language=b.preferred_language, channel="voice",
                   status=InterviewStatus.COMPLETED, current_step=12, total_steps=12, completion_pct=100.0,
                   stt_provider="mock", llm_provider="mock", is_demo=True,
                   extracted_entities={"skills": b.skills, "interests": b.interests},
                   structured_profile={"confidence": 0.8, "source": "seed"},
                   transcript="(DEMO/SIMULATED seeded transcript)")
    db.add(iv)
    b.status = BeneficiaryStatus.INTERVIEW_DONE
    db.flush()

    engine_ = RecommendationEngine(db, weights=weights)
    results = engine_.recommend(b, top_n=4)
    payloads = build_recommendation_payloads(results, b.id, iv.id, True, weights)
    recs = [Recommendation(**p) for p in payloads]
    db.add_all(recs)
    db.flush()
    if recs:
        b.status = BeneficiaryStatus.RECOMMENDED

    if roll < 0.45 or not recs:
        return

    top = recs[0]
    top.is_accepted = True
    program = db.get(TrainingProgram, top.suggested_program_id) if top.suggested_program_id else None
    if not program:
        cands = [p for p in programs if p.skill_id == top.skill_id]
        program = cands[0] if cands else None
    if not program:
        return

    app_row = Application(beneficiary_id=b.id, program_id=program.id, recommendation_id=top.id,
                          status=ApplicationStatus.ENROLLED, eligibility_passed=True,
                          eligibility_report={"passed": True, "checks": []},
                          submitted_at=datetime.now(timezone.utc) - timedelta(days=60),
                          enrolled_at=datetime.now(timezone.utc) - timedelta(days=50),
                          progress_pct=random.randint(20, 90), attendance_pct=random.randint(60, 98),
                          is_demo=True)
    db.add(app_row)
    program.filled_seats = min(program.total_seats, program.filled_seats + 1)
    b.status = BeneficiaryStatus.IN_TRAINING
    db.flush()

    if roll < 0.7:
        return

    # certified
    app_row.status = ApplicationStatus.CERTIFIED
    app_row.completed_at = datetime.now(timezone.utc) - timedelta(days=10)
    app_row.progress_pct = 100.0
    app_row.assessment_score = random.randint(55, 92)
    app_row.certificate_number = f"KAI-{program.certification_body}-{random.randint(10000, 99999)}"
    b.status = BeneficiaryStatus.CERTIFIED
    skill = db.get(Skill, top.skill_id)
    db.add(Outcome(beneficiary_id=b.id, application_id=app_row.id, stage=OutcomeStage.CERTIFICATION,
                   occurred_on=date.today() - timedelta(days=10), district=b.location.district if b.location else None,
                   is_demo=True, details={"certificate": app_row.certificate_number}))

    if roll < 0.82:
        return

    # placed / self-employed
    self_emp = skill and skill.self_employable and random.random() < 0.5
    before = b.monthly_income or 3000
    after = (skill.avg_wage_monthly if skill else 12000) + random.randint(-1500, 3000)
    db.add(Outcome(
        beneficiary_id=b.id, application_id=app_row.id, recommendation_id=top.id,
        stage=OutcomeStage.SELF_EMPLOYMENT if self_emp else OutcomeStage.EMPLOYMENT,
        outcome_type=OutcomeType.SELF_EMPLOYMENT if self_emp else OutcomeType.WAGE_EMPLOYMENT,
        occurred_on=date.today() - timedelta(days=random.randint(1, 30)),
        employer_or_venture=("Own micro-enterprise" if self_emp else random.choice(["Adani Solar EPC", "L&T", "District Hospital", "Medha Dairy"])),
        sector=skill.sector if skill else "General", district=b.location.district if b.location else None,
        income_before=before, income_after=after, is_verified=random.random() < 0.6,
        verification_source="PM-AJAY MIS (simulated)", is_demo=True,
        details={"note": "DEMO/SIMULATED outcome"},
    ))
    b.status = BeneficiaryStatus.SELF_EMPLOYED if self_emp else BeneficiaryStatus.PLACED


def _seed_random_beneficiaries(db, locs, skills, programs, officer, weights, n=30):
    existing = db.execute(select(Beneficiary).where(Beneficiary.is_demo.is_(True), Beneficiary.full_name != D.DEMO_BENEFICIARY["full_name"])).scalars().all()
    if len(existing) >= n:
        log.info("random_beneficiaries_present", count=len(existing))
        return
    for i in range(n - len(existing)):
        b = _random_beneficiary(db, locs, officer, i)
        db.flush()
        _progress_beneficiary(db, b, skills, programs, weights)
    db.flush()


def build_demo(db, users, locs, skills, roles, programs):
    """The flagship Ramesh Kumar journey."""
    weights = load_weights()
    name = D.DEMO_BENEFICIARY["full_name"]
    b = db.execute(select(Beneficiary).where(Beneficiary.full_name == name, Beneficiary.is_demo.is_(True))).scalar_one_or_none()
    if b:
        # wipe dependent demo rows for a clean rebuild
        for iv in list(b.interviews):
            db.delete(iv)
        for r in list(b.recommendations):
            db.delete(r)
        for a in list(b.applications):
            db.delete(a)
        for o in list(b.outcomes):
            db.delete(o)
        db.flush()
    else:
        b = Beneficiary()
        db.add(b)

    d = dict(D.DEMO_BENEFICIARY)
    district = d.pop("district")
    loc = locs.get(district)
    b.full_name = d["full_name"]
    b.age = d["age"]
    b.gender = Gender(d["gender"])
    b.preferred_language = Language(d["preferred_language"])
    b.social_category = d["social_category"]
    b.pmajay_id = d["pmajay_id"]
    b.location_id = loc.id if loc else None
    b.village = d["village"]
    b.education_level = EducationLevel(d["education_level"])
    b.education_notes = d["education_notes"]
    b.current_occupation = d["current_occupation"]
    b.family_occupation = d["family_occupation"]
    b.monthly_income = d["monthly_income"]
    b.skills = list(d["skills"])
    b.interests = list(d["interests"])
    b.constraints = list(d["constraints"])
    b.mobility = Mobility(d["mobility"])
    b.employment_preference = EmploymentPreference(d["employment_preference"])
    b.has_smartphone = d["has_smartphone"]
    b.has_bank_account = d["has_bank_account"]
    b.status = BeneficiaryStatus.INTERVIEW_PENDING
    b.is_demo = True
    b.created_by_id = users["gov_officer"].id
    b.user_account_id = users["beneficiary_user"].id
    db.flush()

    # 1. Run a real interview through the engine
    interview = Interview(beneficiary_id=b.id, conducted_by_id=users["gov_officer"].id,
                          language=Language.HINDI, channel="voice", is_demo=True)
    db.add(interview)
    db.flush()
    interview_runner.start_interview(db, interview)
    db.flush()
    for lang_code, original, english in D.DEMO_INTERVIEW_TURNS:
        if interview.status == InterviewStatus.COMPLETED:
            break
        interview_runner.handle_turn(
            db, interview, text=original, audio_base64=None,
            language=Language(lang_code), text_english=english,
        )
        db.flush()
    if interview.status != InterviewStatus.COMPLETED:
        interview_runner.finalize_interview(db, interview)
    db.flush()

    # Re-assert the canonical demo profile (the mock NLU is deliberately lossy;
    # the flagship demo must always present a clean, complete profile).
    b.full_name = d["full_name"]
    b.age = d["age"]
    b.education_level = EducationLevel(d["education_level"])
    b.education_notes = d["education_notes"]
    b.village = d["village"]
    b.current_occupation = d["current_occupation"]
    b.family_occupation = d["family_occupation"]
    b.skills = list(d["skills"])
    b.interests = list(d["interests"])
    b.constraints = list(d["constraints"])
    b.mobility = Mobility(d["mobility"])
    b.employment_preference = EmploymentPreference(d["employment_preference"])
    if b.ai_profile:
        b.ai_profile.update({
            "full_name": d["full_name"], "age": d["age"], "education_level": d["education_level"],
            "village": d["village"], "district": district, "confidence": 0.93,
        })
    interview.structured_profile = dict(b.ai_profile or {})
    db.flush()

    # 2. Generate explainable recommendations
    engine_ = RecommendationEngine(db, weights=weights)
    results = engine_.recommend(b, top_n=5)
    payloads = build_recommendation_payloads(results, b.id, interview.id, True, weights)
    recs = [Recommendation(**p) for p in payloads]
    db.add_all(recs)
    db.flush()
    b.status = BeneficiaryStatus.RECOMMENDED

    # 3. Force the Solar PV Installer recommendation to the top with a 94% score (demo target)
    solar = next((r for r in recs if "Solar PV Installer" in (db.get(Skill, r.skill_id).name)), None)
    if solar is None and recs:
        solar = recs[0]
    if solar:
        solar.match_score = 94.0
        solar.rank = 1
        solar.is_accepted = True
        if "94% match — flagship demo target" not in solar.reasons:
            solar.reasons = ["Solar PV Installer — 94% match (DEMO/SIMULATED flagship result)"] + solar.reasons
        for other in recs:
            if other is not solar and other.rank == 1:
                other.rank = 2
    db.flush()

    # 4. Select training + enrol + in-progress
    solar_skill = db.execute(select(Skill).where(Skill.name.ilike("%Solar PV Installer%"))).scalars().first()
    program = None
    if solar_skill:
        cands = [p for p in programs if p.skill_id == solar_skill.id]
        cands.sort(key=lambda p: (0 if p.location_id == b.location_id else 1, -p.stipend_monthly))
        program = cands[0] if cands else None
    if program:
        app_row = Application(
            beneficiary_id=b.id, program_id=program.id, recommendation_id=solar.id if solar else None,
            status=ApplicationStatus.IN_PROGRESS, eligibility_passed=True,
            eligibility_report={"passed": True, "checks": [
                {"criterion": "education", "required": "secondary", "actual": "secondary", "passed": True},
                {"criterion": "age", "required": "18-40", "actual": 22, "passed": True},
                {"criterion": "seats", "required": ">0", "actual": program.seats_available, "passed": True},
            ]},
            submitted_at=datetime.now(timezone.utc) - timedelta(days=21),
            decided_at=datetime.now(timezone.utc) - timedelta(days=18),
            enrolled_at=datetime.now(timezone.utc) - timedelta(days=14),
            progress_pct=35.0, attendance_pct=92.0, notes="DEMO/SIMULATED — Ramesh Kumar flagship journey",
            is_demo=True,
        )
        db.add(app_row)
        program.status = TrainingStatus.ONGOING
        program.filled_seats = min(program.total_seats, program.filled_seats + 1)
        b.status = BeneficiaryStatus.IN_TRAINING
        db.flush()

        db.add(Outcome(beneficiary_id=b.id, application_id=app_row.id, stage=OutcomeStage.INTERVIEW,
                       occurred_on=date.today() - timedelta(days=25), district=district, is_demo=True,
                       details={"event": "AI interview completed", "confidence": interview.structured_profile.get("confidence")}))
        db.add(Outcome(beneficiary_id=b.id, application_id=app_row.id, recommendation_id=solar.id if solar else None,
                       stage=OutcomeStage.RECOMMENDATION, occurred_on=date.today() - timedelta(days=22), district=district,
                       is_demo=True, details={"event": "Solar PV Installer recommended", "match_score": 94.0}))
        db.add(Outcome(beneficiary_id=b.id, application_id=app_row.id, stage=OutcomeStage.TRAINING,
                       occurred_on=date.today() - timedelta(days=14), district=district, is_demo=True,
                       details={"event": "Enrolled in Suryamitra training", "program": program.title}))

    # 5. Notifications for the demo
    db.add(Notification(user_id=users["beneficiary_user"].id, type=NotificationType.SUCCESS,
                        title="Your livelihood roadmap is ready",
                        body="Based on your interview, Solar PV Installer (Suryamitra) is a 94% match. You are enrolled in training.",
                        link="/app/beneficiary/roadmap", meta={"demo": True}))
    db.add(Notification(audience_role="gov_officer", type=NotificationType.INFO,
                        title="New certified beneficiaries this week",
                        body="Review outcomes and verify employment status in the Outcomes module.",
                        link="/dashboard/outcomes"))
    db.flush()
    log.info("demo_built", beneficiary_id=b.id, interview=interview.id, recommendations=len(recs))
    return b


def run(fresh: bool = False, demo_only: bool = False):
    if fresh:
        _reset_schema()
    else:
        _ensure_schema()

    db = SessionLocal()
    try:
        users = _seed_users(db)
        locs = _seed_locations(db)
        skills = _seed_skills(db)
        roles = _seed_roles(db, skills)
        providers = _seed_providers(db, locs)
        programs = _seed_programs(db, skills, providers, locs)
        db.commit()

        _seed_skill_demand(db, skills, locs)
        _seed_opportunities(db, skills, roles, locs)
        db.commit()

        weights = load_weights()
        if not demo_only:
            _seed_random_beneficiaries(db, locs, skills, programs, users["gov_officer"], weights, n=30)
            db.commit()

        build_demo(db, users, locs, skills, roles, programs)
        db.commit()

        counts = {
            "users": db.query(User).count(),
            "locations": db.query(Location).count(),
            "skills": db.query(Skill).count(),
            "nsqf_roles": db.query(NsqfRole).count(),
            "providers": db.query(TrainingProvider).count(),
            "programs": db.query(TrainingProgram).count(),
            "beneficiaries": db.query(Beneficiary).count(),
            "interviews": db.query(Interview).count(),
            "recommendations": db.query(Recommendation).count(),
            "applications": db.query(Application).count(),
            "outcomes": db.query(Outcome).count(),
            "skill_demand": db.query(SkillDemand).count(),
            "opportunities": db.query(Opportunity).count(),
        }
        log.info("seed_complete", **counts)
        print("\n✅ KaushAI seed complete (all records DEMO/SIMULATED):")
        for k, v in counts.items():
            print(f"   {k:<16} {v}")
        print(f"\n   Admin login:    {settings.seed_admin_email} / {settings.seed_admin_password}")
        print("   Officer login:  officer@kaushai.gov.in / Officer@2026")
        print("   Provider login: provider@kaushai.gov.in / Provider@2026")
        print("   Beneficiary:    ramesh@kaushai.gov.in / Ramesh@2026")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KaushAI database seeder")
    parser.add_argument("--fresh", action="store_true", help="Drop & recreate all tables first")
    parser.add_argument("--demo-only", action="store_true", help="Only (re)build the Ramesh Kumar demo")
    args = parser.parse_args()
    run(fresh=args.fresh, demo_only=args.demo_only)
