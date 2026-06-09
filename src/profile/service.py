from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.admin.models import City
from src.auth.models import User
from src.profile.models import (
    PersonalStyle,
    PersonalStyleRead,
    Profile,
    ProfileRead,
    ProfileUpdate,
)


def _profile_to_read(profile: Profile) -> ProfileRead:
    return ProfileRead(
        user_id=profile.user_id,
        name=profile.name,
        bio=profile.bio,
        gender=profile.gender,
        city=profile.city_obj.slug if profile.city_obj else None,
        city_id=profile.city_id,
        personal_styles=[
            PersonalStyleRead.model_validate(style, from_attributes=True)
            for style in profile.personal_styles
        ],
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_personal_styles(self) -> list[PersonalStyle]:
        stmt = select(PersonalStyle).order_by(PersonalStyle.display_name)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_profile(self, user: User) -> Profile | None:
        stmt = (
            select(Profile)
            .where(Profile.user_id == user.id)
            .options(
                selectinload(Profile.city_obj),
                selectinload(Profile.personal_styles),
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_or_create_profile(self, user: User) -> Profile:
        profile = await self.get_profile(user)
        if profile is not None:
            return profile

        profile = Profile(user_id=user.id)
        self.session.add(profile)
        await self.session.commit()

        created = await self.get_profile(user)
        if created is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Profile could not be loaded after creation",
            )
        return created

    async def update_profile(self, user: User, data: ProfileUpdate) -> Profile:
        profile = await self.get_or_create_profile(user)
        fields = data.model_dump(exclude_unset=True)

        style_slugs = fields.pop("personal_style_slugs", None)
        city_slug = fields.pop("city", None)

        if city_slug is not None:
            if city_slug == "":
                profile.city_id = None
            else:
                stmt = select(City).where(City.slug == city_slug)
                res = await self.session.execute(stmt)
                city_obj = res.scalar_one_or_none()
                if not city_obj:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"City '{city_slug}' not found",
                    )
                profile.city_id = city_obj.id

        for key, value in fields.items():
            setattr(profile, key, value)

        if style_slugs is not None:
            if not style_slugs:
                profile.personal_styles = []
            else:
                stmt = select(PersonalStyle).where(
                    PersonalStyle.slug.in_(style_slugs)
                )
                res = await self.session.execute(stmt)
                styles = list(res.scalars().all())
                found_slugs = {style.slug for style in styles}
                missing = [slug for slug in style_slugs if slug not in found_slugs]
                if missing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Personal style(s) not found: {', '.join(missing)}",
                    )
                profile.personal_styles = styles

        profile.updated_at = datetime.now(timezone.utc)
        self.session.add(profile)
        await self.session.commit()

        updated = await self.get_profile(user)
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Profile could not be loaded after update",
            )
        return updated
