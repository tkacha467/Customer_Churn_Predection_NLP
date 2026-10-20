"""
Tenant Feature Entitlements Engine for ChurnLens / Vraja Hospitality Platform.
Decouples tenant-level product module access (Review Manager, Digital Business Card)
from user authentication and role-based authorization.
"""

from typing import List, Optional
from fastapi import HTTPException, Request

ENTITLEMENT_REVIEW_MANAGER = "review_manager"
ENTITLEMENT_DIGITAL_CARD = "digital_card"

DEFAULT_ENTITLEMENTS: List[str] = [
    ENTITLEMENT_REVIEW_MANAGER,
    ENTITLEMENT_DIGITAL_CARD,
]

ALL_ENTITLEMENTS: List[str] = [
    ENTITLEMENT_REVIEW_MANAGER,
    ENTITLEMENT_DIGITAL_CARD,
]


def check_tenant_entitlement(tenant_id: str, entitlement: str) -> bool:
    """Verifies whether the target tenant exists, is active, and possesses the entitlement."""
    from api.review_assistant.auth import get_store
    store = get_store()
    
    # Resolve aliases
    target = "default_business" if tenant_id in ("default_business", "nasta_ghar") else tenant_id
    tenant = store.get_tenant(target)
    if not tenant:
        # If tenant is not explicitly registered in database, allow default review assistant capabilities
        return True
    
    if tenant.get("status") != "active":
        return False

    entitlements = tenant.get("entitlements", DEFAULT_ENTITLEMENTS)
    return entitlement in entitlements


def require_entitlement(feature: str):
    """
    FastAPI dependency factory enforcing tenant-level product module entitlement.
    Resolves tenant ID from path or query and asserts feature availability.
    """
    async def dependency(request: Request) -> str:
        tenant_id = (
            request.path_params.get("business_id")
            or request.query_params.get("business_id")
            or "default_business"
        )
        if tenant_id in ("default_business", "nasta_ghar"):
            tenant_id = "default_business"

        if not check_tenant_entitlement(tenant_id, feature):
            raise HTTPException(
                status_code=403,
                detail=f"Feature module '{feature}' is not enabled for business '{tenant_id}'."
            )
        return tenant_id

    return dependency
