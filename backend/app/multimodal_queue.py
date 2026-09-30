from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
import uuid

from .multimodal import process_multimodal_file


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

MAX_WORKERS = 2
BACKGROUND_THRESHOLD_SECONDS = 30
RETENTION_MINUTES = 30

UPLOAD_DIRECTORY = Path("test_files/uploads")
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# BACKGROUND WORKER
# ---------------------------------------------------------

executor = ThreadPoolExecutor(
    max_workers=MAX_WORKERS
)

jobs = {}


# ---------------------------------------------------------
# PROCESS FILE
# ---------------------------------------------------------

def process_file_job(
    job_id,
    file_path,
    customer_message="",
    session_id="",
):
    try:
        jobs[job_id]["status"] = "processing"

        result = process_multimodal_file(
            file_path,
            customer_message=customer_message,
        )

        result["session_id"] = session_id or None
        result["job_id"] = job_id

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = result
        jobs[job_id]["completed_at"] = (
            datetime.now().isoformat(
                timespec="seconds"
            )
        )

        return result

    except Exception as error:

        jobs[job_id]["status"] = "failed"

        jobs[job_id]["error"] = (
            type(error).__name__
        )

        jobs[job_id]["completed_at"] = (
            datetime.now().isoformat(
                timespec="seconds"
            )
        )

        return None


# ---------------------------------------------------------
# SUBMIT BACKGROUND JOB
# ---------------------------------------------------------

def submit_file_job(
    file_path,
    customer_message="",
    session_id="",
):
    job_id = uuid.uuid4().hex

    jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "file_name": Path(file_path).name,
        "created_at": datetime.now().isoformat(
            timespec="seconds"
        ),
        "completed_at": None,
        "result": None,
        "error": None,
    }

    executor.submit(
        process_file_job,
        job_id,
        Path(file_path),
        customer_message,
        session_id,
    )

    return jobs[job_id]


# ---------------------------------------------------------
# GET JOB STATUS
# ---------------------------------------------------------

def get_job_status(job_id):

    job = jobs.get(job_id)

    if job is None:
        return {
            "job_id": job_id,
            "status": "not_found",
        }

    return job


# ---------------------------------------------------------
# DELETE OLD FILES
# ---------------------------------------------------------

def cleanup_expired_files(
    directory=UPLOAD_DIRECTORY,
    retention_minutes=RETENTION_MINUTES,
):
    directory = Path(directory)

    if not directory.exists():
        return []

    cutoff = (
        datetime.now()
        - timedelta(
            minutes=retention_minutes
        )
    )

    deleted_files = []

    for file_path in directory.iterdir():

        if not file_path.is_file():
            continue

        modified_time = datetime.fromtimestamp(
            file_path.stat().st_mtime
        )

        if modified_time < cutoff:

            try:
                file_path.unlink()

                deleted_files.append(
                    file_path.name
                )

            except OSError:
                pass

    return deleted_files


# ---------------------------------------------------------
# CLEAN OLD JOB RECORDS
# ---------------------------------------------------------

def cleanup_old_jobs(
    retention_minutes=RETENTION_MINUTES,
):
    cutoff = (
        datetime.now()
        - timedelta(
            minutes=retention_minutes
        )
    )

    removed_jobs = []

    for job_id, job in list(
        jobs.items()
    ):

        created_at = datetime.fromisoformat(
            job["created_at"]
        )

        if created_at < cutoff:

            del jobs[job_id]

            removed_jobs.append(
                job_id
            )

    return removed_jobs


# ---------------------------------------------------------
# QUEUE STATUS
# ---------------------------------------------------------

def get_queue_status():

    queued = 0
    processing = 0
    completed = 0
    failed = 0

    for job in jobs.values():

        status = job["status"]

        if status == "queued":
            queued += 1

        elif status == "processing":
            processing += 1

        elif status == "completed":
            completed += 1

        elif status == "failed":
            failed += 1

    return {
        "queued": queued,
        "processing": processing,
        "completed": completed,
        "failed": failed,
        "total": len(jobs),
        "max_workers": MAX_WORKERS,
        "background_threshold_seconds":
            BACKGROUND_THRESHOLD_SECONDS,
        "retention_minutes":
            RETENTION_MINUTES,
    }


# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    print(
        "Background multimodal queue loaded."
    )

    print(
        get_queue_status()
    )