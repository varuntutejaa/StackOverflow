from fastapi import APIRouter

from app.api.routes import (
    analytics,
    applications,
    auth,
    beneficiaries,
    interviews,
    locations,
    meta,
    mobile,
    notifications,
    opportunities,
    outcomes,
    recommendations,
    skills,
    training,
    users,
)

api_router = APIRouter()
api_router.include_router(meta.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(locations.router)
api_router.include_router(beneficiaries.router)
api_router.include_router(skills.router)
api_router.include_router(training.router)
api_router.include_router(interviews.router)
api_router.include_router(recommendations.router)
api_router.include_router(applications.router)
api_router.include_router(outcomes.router)
api_router.include_router(opportunities.router)
api_router.include_router(analytics.router)
api_router.include_router(notifications.router)
# The Android app's camelCase surface. Four of its paths collide with the
# dashboard's and are dispatched from those modules instead — see mobile.py.
api_router.include_router(mobile.router)
