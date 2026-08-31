"""Import all models so Alembic + Base.metadata see them."""
from app.db.base import Base  # noqa: F401
from app.models.application import Application  # noqa: F401
from app.models.audit import AuditLog  # noqa: F401
from app.models.beneficiary import Beneficiary  # noqa: F401
from app.models.enums import *  # noqa: F401,F403
from app.models.interview import Interview, InterviewMessage  # noqa: F401
from app.models.location import Location  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.opportunity import Opportunity, SkillDemand  # noqa: F401
from app.models.outcome import Outcome  # noqa: F401
from app.models.recommendation import Recommendation  # noqa: F401
from app.models.skill import NsqfRole, Skill, role_skill_link  # noqa: F401
from app.models.training import TrainingProgram, TrainingProvider  # noqa: F401
from app.models.user import User  # noqa: F401

__all__ = [
    "Base",
    "User",
    "Location",
    "Beneficiary",
    "Skill",
    "NsqfRole",
    "role_skill_link",
    "TrainingProvider",
    "TrainingProgram",
    "Interview",
    "InterviewMessage",
    "Recommendation",
    "Application",
    "Outcome",
    "Opportunity",
    "SkillDemand",
    "Notification",
    "AuditLog",
]
