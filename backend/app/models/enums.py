"""Enumerations shared across models and schemas."""
from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    GOV_OFFICER = "gov_officer"
    TRAINING_PROVIDER = "training_provider"
    BENEFICIARY = "beneficiary"


class Language(str, enum.Enum):
    HINDI = "hi"
    ENGLISH = "en"
    SANTHALI = "sat"
    HO = "hoc"
    MUNDARI = "unr"


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNDISCLOSED = "undisclosed"


class EducationLevel(str, enum.Enum):
    NONE = "none"
    PRIMARY = "primary"          # up to class 5
    MIDDLE = "middle"            # class 6-8
    SECONDARY = "secondary"      # class 10
    SENIOR_SECONDARY = "senior_secondary"  # class 12
    ITI = "iti"
    DIPLOMA = "diploma"
    GRADUATE = "graduate"
    POSTGRADUATE = "postgraduate"


class Mobility(str, enum.Enum):
    LOCAL = "local"              # within village / block
    DISTRICT = "district"
    STATE = "state"
    ANYWHERE = "anywhere"


class EmploymentPreference(str, enum.Enum):
    WAGE_EMPLOYMENT = "wage_employment"
    SELF_EMPLOYMENT = "self_employment"
    APPRENTICESHIP = "apprenticeship"
    ANY = "any"


class BeneficiaryStatus(str, enum.Enum):
    REGISTERED = "registered"
    INTERVIEW_PENDING = "interview_pending"
    INTERVIEW_DONE = "interview_done"
    RECOMMENDED = "recommended"
    IN_TRAINING = "in_training"
    CERTIFIED = "certified"
    PLACED = "placed"
    SELF_EMPLOYED = "self_employed"
    DROPPED_OUT = "dropped_out"
    ARCHIVED = "archived"


class InterviewStatus(str, enum.Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class MessageRole(str, enum.Enum):
    SYSTEM = "system"
    ASSISTANT = "assistant"
    USER = "user"


class ApplicationStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    WAITLISTED = "waitlisted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ENROLLED = "enrolled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CERTIFIED = "certified"
    WITHDRAWN = "withdrawn"


class TrainingStatus(str, enum.Enum):
    UPCOMING = "upcoming"
    OPEN = "open"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OutcomeStage(str, enum.Enum):
    INTERVIEW = "interview"
    RECOMMENDATION = "recommendation"
    TRAINING = "training"
    CERTIFICATION = "certification"
    EMPLOYMENT = "employment"
    SELF_EMPLOYMENT = "self_employment"


class OutcomeType(str, enum.Enum):
    WAGE_EMPLOYMENT = "wage_employment"
    SELF_EMPLOYMENT = "self_employment"
    APPRENTICESHIP = "apprenticeship"
    HIGHER_EDUCATION = "higher_education"
    NOT_PLACED = "not_placed"


class NotificationType(str, enum.Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ALERT = "alert"


DEMO_TAG = "DEMO/SIMULATED"
