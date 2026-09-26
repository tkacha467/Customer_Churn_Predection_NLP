"""
ChurnLens Review Assistant Package.
AI-assisted customer review draft generation, sentiment validation, and Google link redirection.
"""

from api.review_assistant.routes import router as review_router

__all__ = ["review_router"]
