from src.jobs.models import Job, JobType
from src.jobs.tasks import (
    run_dress_analyze,
    run_dress_from_image,
    run_event_suggest_outfits,
    run_outfit_from_images,
)


def enqueue_job(job: Job) -> str:
    """Dispatch a Celery task for the given job. Returns the Celery task id."""
    match job.job_type:
        case JobType.dress_from_image:
            media_id = job.params["media_id"]
            async_result = run_dress_from_image.delay(
                job.id, job.user_id, media_id
            )
        case JobType.dress_analyze:
            dress_id = job.params["dress_id"]
            async_result = run_dress_analyze.delay(job.id, job.user_id, dress_id)
        case JobType.outfit_from_images:
            media_ids = job.params["media_ids"]
            async_result = run_outfit_from_images.delay(
                job.id, job.user_id, media_ids
            )
        case JobType.event_suggest_outfits:
            event_id = job.params["event_id"]
            async_result = run_event_suggest_outfits.delay(
                job.id, job.user_id, event_id
            )
        case _:
            raise ValueError(f"Unknown job type: {job.job_type}")
    return async_result.id
