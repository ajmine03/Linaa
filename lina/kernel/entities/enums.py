"""Shared enumerations used across LINA domain entities."""

from __future__ import annotations

from enum import StrEnum


class EngagementStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EngagementType(StrEnum):
    PENTEST = "pentest"
    BUG_BOUNTY = "bug_bounty"
    RED_TEAM = "red_team"
    DFIR = "dfir"
    BLUE_TEAM = "blue_team"
    AUDIT = "audit"
    RESEARCH_LAB = "research_lab"


class TargetType(StrEnum):
    HOST = "host"
    IP_RANGE = "ip_range"
    DOMAIN = "domain"
    URL = "url"
    CLOUD_ACCOUNT = "cloud_account"
    REPOSITORY = "repository"
    MOBILE_APP = "mobile_app"
    WIRELESS_NETWORK = "wireless_network"
    AD_DOMAIN = "ad_domain"
    CONTAINER_IMAGE = "container_image"
    FILE = "file"


class FindingSeverity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingStatus(StrEnum):
    OPEN = "open"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    REMEDIATED = "remediated"
    ACCEPTED_RISK = "accepted_risk"
    DUPLICATE = "duplicate"


class ToolExecutionStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class ToolRiskLevel(StrEnum):
    """Risk classification used by the Authorization Framework to gate execution."""

    READ_ONLY = "read_only"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    DESTRUCTIVE = "destructive"


class AgentSessionStatus(StrEnum):
    INITIALIZING = "initializing"
    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    WAITING_FOR_INPUT = "waiting_for_input"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class AssetType(StrEnum):
    HOST = "host"
    SERVICE = "service"
    WEB_APPLICATION = "web_application"
    CREDENTIAL = "credential"
    CLOUD_RESOURCE = "cloud_resource"
    AD_OBJECT = "ad_object"
    CONTAINER = "container"
    MOBILE_APP = "mobile_app"
    WIRELESS_AP = "wireless_ap"
    FILE_ARTIFACT = "file_artifact"


class CredentialType(StrEnum):
    PASSWORD = "password"
    HASH = "hash"
    API_KEY = "api_key"
    TOKEN = "token"
    SSH_KEY = "ssh_key"
    CERTIFICATE = "certificate"
    KERBEROS_TICKET = "kerberos_ticket"


class ReportFormat(StrEnum):
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    JSON = "json"
    DOCX = "docx"


class EventSeverity(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"