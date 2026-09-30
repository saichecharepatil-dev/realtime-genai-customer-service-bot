from datetime import datetime, time


# ==================================================
# Scheduling Configuration
# ==================================================

SCHEDULE_ENABLED = True

# Pipeline is allowed to run during this time window.
SCHEDULE_START = time(9, 0)
SCHEDULE_END = time(18, 0)

# Maintenance window.
# During maintenance, KB updates should not be activated.
MAINTENANCE_ENABLED = True
MAINTENANCE_START = time(13, 0)
MAINTENANCE_END = time(14, 0)


# ==================================================
# Check Time Window
# ==================================================

def is_time_in_window(current_time, start_time, end_time):
    """
    Check whether the current time is inside a configured window.
    Supports normal and overnight windows.
    """

    if start_time <= end_time:
        return start_time <= current_time <= end_time

    # Overnight window, for example 22:00 -> 06:00
    return current_time >= start_time or current_time <= end_time


# ==================================================
# Check Pipeline Schedule
# ==================================================

def is_schedule_allowed(current_time=None):
    """
    Return True when the pipeline is allowed to run.
    """

    if not SCHEDULE_ENABLED:
        return True

    if current_time is None:
        current_time = datetime.now().time()

    return is_time_in_window(
        current_time,
        SCHEDULE_START,
        SCHEDULE_END
    )


# ==================================================
# Check Maintenance Window
# ==================================================

def is_maintenance_window(current_time=None):
    """
    Return True when the system is currently in maintenance.
    """

    if not MAINTENANCE_ENABLED:
        return False

    if current_time is None:
        current_time = datetime.now().time()

    return is_time_in_window(
        current_time,
        MAINTENANCE_START,
        MAINTENANCE_END
    )


# ==================================================
# Final Pipeline Permission
# ==================================================

def can_run_pipeline(current_time=None):
    """
    Determine whether the knowledge-base pipeline
    can run at the current time.
    """

    if current_time is None:
        current_time = datetime.now().time()

    if not is_schedule_allowed(current_time):
        return {
            "allowed": False,
            "reason": "Outside configured pipeline schedule.",
            "maintenance": False
        }

    if is_maintenance_window(current_time):
        return {
            "allowed": False,
            "reason": "Pipeline is currently inside the maintenance window.",
            "maintenance": True
        }

    return {
        "allowed": True,
        "reason": "Pipeline is allowed to run.",
        "maintenance": False
    }


# ==================================================
# Configuration Report
# ==================================================

def get_schedule_configuration():
    """
    Return the current scheduling configuration.
    """

    return {
        "schedule_enabled": SCHEDULE_ENABLED,
        "schedule_start": SCHEDULE_START.strftime("%H:%M"),
        "schedule_end": SCHEDULE_END.strftime("%H:%M"),
        "maintenance_enabled": MAINTENANCE_ENABLED,
        "maintenance_start": MAINTENANCE_START.strftime("%H:%M"),
        "maintenance_end": MAINTENANCE_END.strftime("%H:%M")
    }


# ==================================================
# Test
# ==================================================

if __name__ == "__main__":

    print("=" * 60)
    print("KNOWLEDGE BASE SCHEDULE CONFIGURATION")
    print("=" * 60)

    configuration = get_schedule_configuration()

    print("\nSchedule enabled:",
          configuration["schedule_enabled"])

    print(
        "Pipeline schedule:",
        configuration["schedule_start"],
        "to",
        configuration["schedule_end"]
    )

    print(
        "Maintenance enabled:",
        configuration["maintenance_enabled"]
    )

    print(
        "Maintenance window:",
        configuration["maintenance_start"],
        "to",
        configuration["maintenance_end"]
    )

    print("\nCurrent time:",
          datetime.now().strftime("%H:%M:%S"))

    result = can_run_pipeline()

    print("\nPipeline status:")

    if result["allowed"]:
        print("  ALLOWED")
    else:
        print("  BLOCKED")

    print("Reason:", result["reason"])

    print("\n" + "=" * 60)