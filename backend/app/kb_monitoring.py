from datetime import datetime
from pathlib import Path
import json
import time


# ==================================================
# Monitoring Paths
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[2]

KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"

MONITORING_STATE_FILE = (
    KNOWLEDGE_BASE_DIR / ".kb_monitoring_state.json"
)


# ==================================================
# Monitoring Configuration
# ==================================================

LATENCY_WARNING_SECONDS = 5.0

CONFIDENCE_WARNING_THRESHOLD = 0.70

ESCALATION_WARNING_THRESHOLD = 1


# ==================================================
# Load Monitoring State
# ==================================================

def load_monitoring_state():
    """
    Load previously recorded monitoring metrics.
    """

    if not MONITORING_STATE_FILE.exists():
        return {
            "runs": [],
            "totals": {
                "successful_runs": 0,
                "failed_runs": 0,
                "total_runs": 0,
                "total_escalations": 0,
                "low_confidence_events": 0
            }
        }

    try:
        with open(
            MONITORING_STATE_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except Exception:
        return {
            "runs": [],
            "totals": {
                "successful_runs": 0,
                "failed_runs": 0,
                "total_runs": 0,
                "total_escalations": 0,
                "low_confidence_events": 0
            }
        }


# ==================================================
# Save Monitoring State
# ==================================================

def save_monitoring_state(state):

    KNOWLEDGE_BASE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        MONITORING_STATE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            state,
            file,
            indent=4
        )


# ==================================================
# Start Timer
# ==================================================

def start_timer():
    """
    Start a high-resolution execution timer.
    """

    return time.perf_counter()


# ==================================================
# Calculate Latency
# ==================================================

def calculate_latency(start_time):
    """
    Calculate execution latency in seconds.
    """

    return round(
        time.perf_counter() - start_time,
        4
    )


# ==================================================
# Record Pipeline Run
# ==================================================

def record_pipeline_run(
    status,
    latency_seconds,
    failures=None,
    confidence=None,
    escalations=0,
    health_status=None
):
    """
    Record one pipeline execution.

    status:
        success / failed / blocked

    confidence:
        Optional confidence value between 0 and 1.

    escalations:
        Number of escalation events.
    """

    if failures is None:
        failures = []

    state = load_monitoring_state()

    if "runs" not in state:
        state["runs"] = []

    if "totals" not in state:
        state["totals"] = {
            "successful_runs": 0,
            "failed_runs": 0,
            "total_runs": 0,
            "total_escalations": 0,
            "low_confidence_events": 0
        }

    confidence_warning = False

    if confidence is not None:

        try:
            confidence_value = float(confidence)

            if confidence_value < CONFIDENCE_WARNING_THRESHOLD:
                confidence_warning = True
                state["totals"]["low_confidence_events"] += 1

        except (TypeError, ValueError):

            confidence = None

    run_record = {
        "timestamp": datetime.now().isoformat(
            timespec="seconds"
        ),
        "status": status,
        "latency_seconds": latency_seconds,
        "failures": failures,
        "confidence": confidence,
        "confidence_warning": confidence_warning,
        "escalations": escalations,
        "health_status": health_status
    }

    state["runs"].append(run_record)

    # Keep only the latest 100 monitoring records.
    state["runs"] = state["runs"][-100:]

    state["totals"]["total_runs"] += 1

    if status == "success":
        state["totals"]["successful_runs"] += 1

    elif status == "failed":
        state["totals"]["failed_runs"] += 1

    state["totals"]["total_escalations"] += escalations

    save_monitoring_state(state)

    return run_record


# ==================================================
# Generate Monitoring Alerts
# ==================================================

def generate_monitoring_alerts(
    latency_seconds,
    failures=None,
    confidence=None,
    escalations=0,
    health_status=None
):
    """
    Generate monitoring alerts based on configured thresholds.
    """

    if failures is None:
        failures = []

    alerts = []

    # ----------------------------------------------
    # Latency
    # ----------------------------------------------

    if latency_seconds > LATENCY_WARNING_SECONDS:

        alerts.append({
            "type": "latency",
            "severity": "warning",
            "message": (
                "Pipeline latency exceeded the configured "
                "warning threshold."
            )
        })

    # ----------------------------------------------
    # Failures
    # ----------------------------------------------

    if failures:

        alerts.append({
            "type": "pipeline_failure",
            "severity": "error",
            "message": (
                f"{len(failures)} pipeline failure(s) detected."
            )
        })

    # ----------------------------------------------
    # Confidence
    # ----------------------------------------------

    if confidence is not None:

        try:

            confidence_value = float(confidence)

            if confidence_value < CONFIDENCE_WARNING_THRESHOLD:

                alerts.append({
                    "type": "low_confidence",
                    "severity": "warning",
                    "message": (
                        "Response confidence is below the "
                        "configured threshold."
                    )
                })

        except (TypeError, ValueError):
            pass

    # ----------------------------------------------
    # Escalations
    # ----------------------------------------------

    if escalations >= ESCALATION_WARNING_THRESHOLD:

        alerts.append({
            "type": "escalation",
            "severity": "warning",
            "message": (
                f"{escalations} escalation event(s) detected."
            )
        })

    # ----------------------------------------------
    # Health
    # ----------------------------------------------

    if health_status in {
        "unhealthy",
        "rollback_failed",
        "rollback_failed_health_check"
    }:

        alerts.append({
            "type": "health",
            "severity": "critical",
            "message": (
                f"Knowledge-base health status: "
                f"{health_status}"
            )
        })

    return alerts


# ==================================================
# Monitoring Summary
# ==================================================

def get_monitoring_summary():

    state = load_monitoring_state()

    totals = state.get(
        "totals",
        {}
    )

    total_runs = totals.get(
        "total_runs",
        0
    )

    successful_runs = totals.get(
        "successful_runs",
        0
    )

    failed_runs = totals.get(
        "failed_runs",
        0
    )

    if total_runs > 0:

        success_rate = round(
            successful_runs / total_runs * 100,
            2
        )

    else:

        success_rate = 0.0

    recent_runs = state.get(
        "runs",
        []
    )

    latencies = [
        run["latency_seconds"]
        for run in recent_runs
        if isinstance(
            run.get("latency_seconds"),
            (int, float)
        )
    ]

    if latencies:

        average_latency = round(
            sum(latencies) / len(latencies),
            4
        )

        maximum_latency = max(latencies)

    else:

        average_latency = 0.0
        maximum_latency = 0.0

    return {
        "total_runs": total_runs,
        "successful_runs": successful_runs,
        "failed_runs": failed_runs,
        "success_rate_percent": success_rate,
        "average_latency_seconds": average_latency,
        "maximum_latency_seconds": maximum_latency,
        "total_escalations": totals.get(
            "total_escalations",
            0
        ),
        "low_confidence_events": totals.get(
            "low_confidence_events",
            0
        )
    }


# ==================================================
# Print Monitoring Report
# ==================================================

def print_monitoring_report():

    summary = get_monitoring_summary()

    print("\n")
    print("=" * 60)
    print("KNOWLEDGE BASE MONITORING REPORT")
    print("=" * 60)

    print(
        f"\nTotal runs: "
        f"{summary['total_runs']}"
    )

    print(
        f"Successful runs: "
        f"{summary['successful_runs']}"
    )

    print(
        f"Failed runs: "
        f"{summary['failed_runs']}"
    )

    print(
        f"Success rate: "
        f"{summary['success_rate_percent']}%"
    )

    print(
        f"Average latency: "
        f"{summary['average_latency_seconds']} seconds"
    )

    print(
        f"Maximum latency: "
        f"{summary['maximum_latency_seconds']} seconds"
    )

    print(
        f"Total escalations: "
        f"{summary['total_escalations']}"
    )

    print(
        f"Low-confidence events: "
        f"{summary['low_confidence_events']}"
    )

    print("\n" + "=" * 60)


# ==================================================
# Test Monitoring
# ==================================================

if __name__ == "__main__":

    print("KNOWLEDGE BASE MONITORING TEST")
    print("--------------------------------")

    start = start_timer()

    # Simulated pipeline work
    time.sleep(0.1)

    latency = calculate_latency(start)

    test_record = record_pipeline_run(
        status="success",
        latency_seconds=latency,
        failures=[],
        confidence=0.92,
        escalations=0,
        health_status="healthy"
    )

    print("\nRecorded run:")
    print(test_record)

    alerts = generate_monitoring_alerts(
        latency_seconds=latency,
        failures=[],
        confidence=0.92,
        escalations=0,
        health_status="healthy"
    )

    print("\nAlerts:")

    if alerts:
        for alert in alerts:
            print(alert)
    else:
        print("None")

    print_monitoring_report()