import streamlit as st
import os
from enum import Enum

class AppConfig:
    APP_NAME = "Production Planner"
    VERSION = "1.0.0"
    
    # Supabase Secrets
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    WORKER = "worker"
    VIEWER = "viewer"

class StepStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    PROBLEM = "problem"

STATUS_LABELS = {
    StepStatus.NOT_STARTED: "Не розпочато",
    StepStatus.IN_PROGRESS: "В роботі",
    StepStatus.DONE: "Виконано",
    StepStatus.PROBLEM: "Проблема"
}

ROLE_LABELS = {
    UserRole.ADMIN: "Адміністратор",
    UserRole.MANAGER: "Менеджер",
    UserRole.WORKER: "Працівник",
    UserRole.VIEWER: "Спостерігач"
}
