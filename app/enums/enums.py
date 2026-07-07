from enum import Enum

class UserRole(str,Enum):
    ##ALL VALID ROLES FOR USERS

    SUPER_ADMIN = "SUPER_ADMIN"
    ORG_ADMIN = "ORG_ADMIN"
    EMPLOYEE = "EMPLOYEE"


class DocumentStatus(str, Enum):
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"

class DocumentType(str,Enum):
    HR_POLICY="HR_POLICY"
    SOP="SOP"
    TECHNICAL="TECHNICAL"
    MEETING_NOTE="MEETING_NOTE"
    REPORT="REPORT"

class FeedbackType(str,Enum):
    Good="Good"
    Satisfactory="Satisfactory"
    Bad="Bad"

# class DepartmentType(str, Enum):
#     HR = "HR"
#     IT = "IT"
#     FINANCE = "Finance"
#     SALES = "Sales"
#     MARKETING = "Marketing"
#     OPERATIONS = "Operations"
#     CUSTOMER_SUPPORT = "Customer Support"
#     ADMINISTRATION = "Administration"
#     LEGAL = "Legal"
#     PROCUREMENT = "Procurement"
#     RESEARCH_AND_DEVELOPMENT = "Research & Development"    

class PrincipalType(str, Enum):
    USER = "USER"
    TEAM = "TEAM"
    DEPARTMENT = "DEPARTMENT"
    ROLE = "ROLE"


class PermissionType(str, Enum):
    READ = "READ"