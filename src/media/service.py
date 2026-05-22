import logging
import uuid
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.auth.models import User
from src.core.config import config
from src.core.models import IPageResponse
from src.core.pagination import paginate
from src.dress.models import Dress
from src.media.models import Media, MediaUpdate, ProcessingStatus

logger = logging.getLogger(__name__)


_EXT_BY_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class MediaService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upload(
        self,
        user: User,
        file: UploadFile,
        dress_id: Optional[int] = None,
    ) -> Media:
        if file.content_type not in config.allowed_image_mimes:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported mime type: {file.content_type}",
            )

        content = await file.read()
        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty",
            )
        if len(content) > config.max_upload_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds {config.max_upload_bytes} bytes",
            )

        if dress_id is not None:
            dress = await self.session.get(Dress, dress_id)
            if dress is None or dress.user_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dress not found",
                )

        ext = _EXT_BY_MIME[file.content_type]
        user_dir = config.upload_dir / str(user.id)
        user_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid.uuid4().hex}{ext}"
        path = user_dir / filename

        path.write_bytes(content)

        width, height = _read_dimensions(path)

        media = Media(
            user_id=user.id,
            dress_id=dress_id,
            storage_path=str(path),
            original_filename=file.filename or filename,
            mime_type=file.content_type,
            size_bytes=len(content),
            width=width,
            height=height,
            processing_status=ProcessingStatus.pending,
        )
        self.session.add(media)
        await self.session.commit()
        await self.session.refresh(media)
        return media

    async def get_for_user(self, user: User, media_id: int) -> Media:
        media = await self.session.get(Media, media_id)
        if media is None or media.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found",
            )
        return media

    async def list_for_user(
        self,
        user: User,
        page: int = 1,
        page_size: int = 20,
        dress_id: Optional[int] = None,
        unassigned: bool = False,
    ) -> IPageResponse[list[Media]]:
        stmt = select(Media).where(Media.user_id == user.id)
        if unassigned:
            stmt = stmt.where(Media.dress_id.is_(None))
        elif dress_id is not None:
            stmt = stmt.where(Media.dress_id == dress_id)
        stmt = stmt.order_by(Media.sort_order, Media.id)
        return await paginate(self.session, stmt, page, page_size)

    async def update(
        self, user: User, media_id: int, data: MediaUpdate
    ) -> Media:
        media = await self.get_for_user(user, media_id)

        if data.unassign:
            media.dress_id = None
        elif data.dress_id is not None:
            dress = await self.session.get(Dress, data.dress_id)
            if dress is None or dress.user_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dress not found",
                )
            media.dress_id = data.dress_id

        if data.sort_order is not None:
            media.sort_order = data.sort_order

        self.session.add(media)
        await self.session.commit()
        await self.session.refresh(media)
        return media

    async def clone_for_dress(self, user: User, source: Media, dress_id: int) -> Media:
        """Link the same on-disk file to another dress via a new media row."""
        dress = await self.session.get(Dress, dress_id)
        if dress is None or dress.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dress not found",
            )
        media = Media(
            user_id=user.id,
            dress_id=dress_id,
            storage_path=source.storage_path,
            original_filename=source.original_filename,
            mime_type=source.mime_type,
            size_bytes=source.size_bytes,
            width=source.width,
            height=source.height,
            sort_order=source.sort_order,
            processing_status=source.processing_status,
            processing_error=source.processing_error,
        )
        self.session.add(media)
        await self.session.flush()
        await self.session.refresh(media)
        return media

    async def _storage_path_in_use(
        self, storage_path: str, exclude_media_id: int
    ) -> bool:
        stmt = (
            select(Media.id)
            .where(Media.storage_path == storage_path)
            .where(Media.id != exclude_media_id)
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def delete(self, user: User, media_id: int) -> None:
        media = await self.get_for_user(user, media_id)
        path = Path(media.storage_path)
        still_used = await self._storage_path_in_use(
            media.storage_path, exclude_media_id=media.id
        )
        await self.session.delete(media)
        await self.session.commit()
        if still_used:
            return
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            logger.warning("Failed to delete file %s: %s", path, exc)


def _read_dimensions(path: Path) -> tuple[Optional[int], Optional[int]]:
    try:
        with Image.open(path) as img:
            return img.width, img.height
    except (UnidentifiedImageError, OSError) as exc:
        logger.warning("Could not read image dimensions for %s: %s", path, exc)
        return None, None
