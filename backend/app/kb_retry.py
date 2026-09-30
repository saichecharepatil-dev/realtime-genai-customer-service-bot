from datetime import datetime, timedelta


# ==================================================
# Retry Configuration
# ==================================================

RETRY_DELAYS_MINUTES = [15, 30, 60]


# ==================================================
# Create Retry Schedule
# ==================================================

def create_retry_schedule(start_time=None):
    """
    Create the retry schedule using the configured
    delays of 15, 30 and 60 minutes.
    """

    if start_time is None:
        start_time = datetime.now()

    retries = []

    for attempt, delay in enumerate(
        RETRY_DELAYS_MINUTES,
        start=1
    ):
        retry_time = (
            start_time
            + timedelta(minutes=delay)
        )

        retries.append({
            "attempt": attempt,
            "delay_minutes": delay,
            "retry_time": retry_time.isoformat(
                timespec="seconds"
            )
        })

    return retries


# ==================================================
# Get Next Retry
# ==================================================

def get_next_retry(
    failed_at,
    completed_attempts
):
    """
    Return the next retry after a failure.

    completed_attempts represents the number of
    retries already attempted.
    """

    if completed_attempts >= len(
        RETRY_DELAYS_MINUTES
    ):
        return None

    delay = RETRY_DELAYS_MINUTES[
        completed_attempts
    ]

    retry_time = (
        failed_at
        + timedelta(minutes=delay)
    )

    return {
        "attempt": completed_attempts + 1,
        "delay_minutes": delay,
        "retry_time": retry_time.isoformat(
            timespec="seconds"
        )
    }


# ==================================================
# Retry Status
# ==================================================

def get_retry_status(
    failed_at,
    completed_attempts,
    current_time=None
):
    """
    Determine whether the next retry is due.
    """

    if current_time is None:
        current_time = datetime.now()

    next_retry = get_next_retry(
        failed_at,
        completed_attempts
    )

    if next_retry is None:

        return {
            "retry_available": False,
            "retry_due": False,
            "message": (
                "Maximum retry attempts reached."
            ),
            "next_retry": None
        }

    retry_time = datetime.fromisoformat(
        next_retry["retry_time"]
    )

    retry_due = current_time >= retry_time

    return {
        "retry_available": True,
        "retry_due": retry_due,
        "message": (
            "Retry is due."
            if retry_due
            else "Retry is waiting."
        ),
        "next_retry": next_retry
    }


# ==================================================
# Print Retry Schedule
# ==================================================

def print_retry_schedule(
    start_time=None
):

    if start_time is None:
        start_time = datetime.now()

    schedule = create_retry_schedule(
        start_time
    )

    print("\n")
    print("=" * 60)
    print("KNOWLEDGE BASE RETRY SCHEDULE")
    print("=" * 60)

    print(
        "\nFailure time:",
        start_time.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    for retry in schedule:

        print(
            f"\nAttempt {retry['attempt']}"
        )

        print(
            f"Delay: "
            f"{retry['delay_minutes']} minutes"
        )

        print(
            f"Retry time: "
            f"{retry['retry_time']}"
        )

    print("\n" + "=" * 60)


# ==================================================
# Test
# ==================================================

if __name__ == "__main__":

    print_retry_schedule()