"""Authentication API endpoints."""

import logging
from fastapi import APIRouter, HTTPException, status

from app.models.schemas import (
    LoginRequest,
    LoginResponse,
    OnboardingRequest,
    OnboardingResponse,
    ProfileResponse,
    ProfileUpdateRequest,
    ProfileUpdateResponse
)
from app.core.profile_store import profile_store

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Check if user exists by name.

    - If exists: Return profile
    - If not: Indicate onboarding required
    """
    logger.info(f"Login attempt: {request.name}")

    exists = await profile_store.exists(request.name)

    if exists:
        profile = await profile_store.load(request.name)
        return LoginResponse(
            status="existing",
            profile=profile,
            requires_onboarding=False
        )
    else:
        return LoginResponse(
            status="new",
            profile=None,
            requires_onboarding=True
        )


@router.post("/onboard", response_model=OnboardingResponse)
async def onboard(request: OnboardingRequest):
    """
    Create a new user profile.

    - Validates input
    - Calculates daily targets
    - Saves profile to JSON
    """
    logger.info(f"Onboarding: {request.name}")

    try:
        profile = await profile_store.create(request)
        return OnboardingResponse(
            profile=profile,
            daily_targets=profile.daily_targets
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Onboarding error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create profile"
        )


@router.get("/profile/{name}", response_model=ProfileResponse)
async def get_profile(name: str):
    """Get user profile by name."""
    logger.info(f"Get profile: {name}")

    profile = await profile_store.load(name)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{name}' not found"
        )

    return ProfileResponse(profile=profile)


@router.patch("/profile/{name}", response_model=ProfileUpdateResponse)
async def update_profile(name: str, request: ProfileUpdateRequest):
    """Update user profile (partial update)."""
    logger.info(f"Update profile: {name}")

    try:
        # Get only fields that were actually provided
        updates = request.model_dump(exclude_unset=True)

        profile = await profile_store.update(name, updates)

        return ProfileUpdateResponse(
            profile=profile,
            updated_fields=list(updates.keys())
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
