from pathlib import Path
from datetime import datetime, date, timedelta
import hashlib
import json
import shutil
import re

from .kb_regression import run_all_regression_tests
from .kb_schedule import can_run_pipeline, get_schedule_configuration
from .kb_retry import get_retry_status
from .kb_access_control import (
    get_current_role,
    require_permission,
    get_access_summary,
)
from .kb_security import mask_sensitive_data, mask_sensitive_dict
from .kb_monitoring import (
    start_timer,
    calculate_latency,
    record_pipeline_run,
    generate_monitoring_alerts,
    print_monitoring_report,
)
# ==================================================
# Project Paths
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[2]

KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
STATE_FILE = KNOWLEDGE_BASE_DIR / ".kb_state.json"
RETRY_STATE_FILE = KNOWLEDGE_BASE_DIR / ".kb_retry_state.json"
HEALTH_STATE_FILE = KNOWLEDGE_BASE_DIR / ".kb_health_state.json"
HEALTH_FAILURE_LIMIT_MINUTES = 5

# ==================================================
# Security Configuration
# ==================================================

ACCESS_CONTROL_ENABLED = True

QUARANTINE_DIR = KNOWLEDGE_BASE_DIR / "quarantine"
VERSIONS_DIR = KNOWLEDGE_BASE_DIR / "versions"


# ==================================================
# Required Metadata
# ==================================================

REQUIRED_METADATA = [
    "version",
    "product",
    "region",
    "access_level",
    "effective_date",
    "expiry_date"
]


# ==================================================
# Quality Rules
# ==================================================

MIN_CONTENT_LENGTH = 30

PROMPT_INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all previous instructions",
    "reveal system prompt",
    "show system prompt",
    "override system instructions",
    "bypass security",
    "disable safety",
    "you are now an administrator",
    "follow these instructions instead",
    "disregard previous instructions",
]
# ==================================================
# Access Control Helper
# ==================================================

def check_permission(permission, role=None):
    """
    Verify that the current role has the required permission.
    """

    if not ACCESS_CONTROL_ENABLED:
        return True

    if role is None:
        role = get_current_role()

    require_permission(role, permission)

    return True

# ==================================================
# Calculate File Hash
# ==================================================

def calculate_file_hash(file_path):

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:

        while True:

            chunk = file.read(8192)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


# ==================================================
# Load Previous Pipeline State
# ==================================================

def load_state():

    if not STATE_FILE.exists():
        return {}

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        return {}


# ==================================================
# Save Pipeline State
# ==================================================

def save_state(state):

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            state,
            file,
            indent=4
        )


# ==================================================
# Parse Metadata
# ==================================================

def parse_metadata(file_path):

    metadata = {}

    try:

        text = file_path.read_text(
            encoding="utf-8"
        )

    except Exception as error:

        return None, f"File cannot be read: {error}"

    if not text.strip():

        return None, "File is empty."

    parts = text.split(
        "\n\n",
        1
    )

    metadata_section = parts[0]

    for line in metadata_section.splitlines():

        if ":" not in line:
            continue

        key, value = line.split(
            ":",
            1
        )

        key = key.strip()
        value = value.strip()

        if key != "METADATA":

            metadata[key] = value

    return metadata, None


# ==================================================
# Get Document Content
# ==================================================

def get_document_content(file_path):

    try:

        text = file_path.read_text(
            encoding="utf-8"
        )

    except Exception as error:

        return None, f"File cannot be read: {error}"

    parts = text.split(
        "\n\n",
        1
    )

    if len(parts) < 2:

        return "", None

    return parts[1].strip(), None


# ==================================================
# Detect Prompt Injection
# ==================================================

def contains_prompt_injection(text):

    text = text.lower()

    return any(
        pattern in text
        for pattern in PROMPT_INJECTION_PATTERNS
    )


# ==================================================
# Validate Document
# ==================================================

def validate_document(file_path):

    metadata, error = parse_metadata(
        file_path
    )

    if error:

        return False, error

    missing_fields = [
        field
        for field in REQUIRED_METADATA
        if not metadata.get(field)
    ]

    if missing_fields:

        return (
            False,
            "Missing required metadata: "
            + ", ".join(missing_fields)
        )

    try:

        float(metadata["version"])

    except ValueError:

        return (
            False,
            "Invalid version value."
        )

    try:

        effective_date = date.fromisoformat(
            metadata["effective_date"]
        )

        expiry_date = date.fromisoformat(
            metadata["expiry_date"]
        )

    except ValueError:

        return (
            False,
            "Invalid effective_date or expiry_date."
        )

    if effective_date > expiry_date:

        return (
            False,
            "effective_date cannot be after expiry_date."
        )

    return True, None


# ==================================================
# Quality Check
# ==================================================

def run_quality_checks(file_path):

    failures = []

    valid, validation_error = validate_document(
        file_path
    )

    if not valid:

        failures.append(
            validation_error
        )

        return {
            "passed": False,
            "failures": failures
        }

    content, content_error = get_document_content(
        file_path
    )

    if content_error:

        failures.append(
            content_error
        )

        return {
            "passed": False,
            "failures": failures
        }

    if not content.strip():

        failures.append(
            "Knowledge content is empty."
        )

    elif len(content.strip()) < MIN_CONTENT_LENGTH:

        failures.append(
            "Knowledge content is too short."
        )

    if contains_prompt_injection(content):

        failures.append(
            "Prompt injection instruction detected."
        )

    suspicious_pattern = re.search(
        r"<script|javascript:|data:text/html",
        content.lower()
    )

    if suspicious_pattern:

        failures.append(
            "Suspicious executable content detected."
        )

    return {
        "passed": len(failures) == 0,
        "failures": failures
    }


# ==================================================
# Quarantine File
# ==================================================

def quarantine_file(
    file_path,
    reason,
    role=None
):
    check_permission("kb_quarantine", role)

    QUARANTINE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    destination = (
        QUARANTINE_DIR
        / file_path.name
    )

    if destination.exists():

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        destination = (
            QUARANTINE_DIR
            / f"{file_path.stem}_{timestamp}"
            f"{file_path.suffix}"
        )

    shutil.move(
        str(file_path),
        str(destination)
    )

    return {
        "file": file_path.name,
        "quarantine_path": str(destination),
        "reason": reason
    }


# ==================================================
# Version Directory
# ==================================================

def get_version_directory(file_path):

    return (
        VERSIONS_DIR
        / file_path.stem
    )


# ==================================================
# Save Known-Good Version
# ==================================================

def save_known_good_version(file_path):

    version_dir = get_version_directory(
        file_path
    )

    version_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    known_good_path = (
        version_dir
        / f"{file_path.stem}_known_good"
        f"{file_path.suffix}"
    )

    shutil.copy2(
        str(file_path),
        str(known_good_path)
    )

    return known_good_path


# ==================================================
# Backup Previous Version
# ==================================================

def backup_previous_version(
    file_path,
    previous_hash
):

    version_dir = get_version_directory(
        file_path
    )

    version_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_name = (
        f"{file_path.stem}_"
        f"{timestamp}_"
        f"{previous_hash[:12]}"
        f"{file_path.suffix}"
    )

    backup_path = (
        version_dir
        / backup_name
    )

    known_good_path = (
        version_dir
        / f"{file_path.stem}_known_good"
        f"{file_path.suffix}"
    )

    if known_good_path.exists():

        shutil.copy2(
            str(known_good_path),
            str(backup_path)
        )

    else:

        shutil.copy2(
            str(file_path),
            str(backup_path)
        )

    return backup_path


# ==================================================
# Find Latest Backup
# ==================================================

def find_latest_backup(file_path):

    version_dir = get_version_directory(
        file_path
    )

    if not version_dir.exists():

        return None

    backups = []

    for backup in version_dir.glob(
        f"{file_path.stem}_*.txt"
    ):

        if backup.name.endswith(
            "_known_good.txt"
        ):

            continue

        if "before_rollback" in backup.name:

            continue

        backups.append(
            backup
        )

    if not backups:

        return None

    backups.sort(
        key=lambda path: path.stat().st_mtime,
        reverse=True
    )

    return backups[0]


# ==================================================
# Rollback File
# ==================================================

def rollback_file(file_name, role=None):

    check_permission("kb_rollback", role)

    target_file = (
        KNOWLEDGE_BASE_DIR
        / file_name
    )

    if not target_file.exists():

        return {
            "success": False,
            "file": file_name,
            "reason": "Target file does not exist."
        }

    backup_path = find_latest_backup(
        target_file
    )

    if backup_path is None:

        return {
            "success": False,
            "file": file_name,
            "reason": "No previous version backup found."
        }

    quality_result = run_quality_checks(
        backup_path
    )

    if not quality_result["passed"]:

        return {
            "success": False,
            "file": file_name,
            "backup": str(backup_path),
            "reason": (
                "Backup quality validation failed: "
                + "; ".join(
                    quality_result["failures"]
                )
            )
        }

    version_dir = get_version_directory(
        target_file
    )

    safety_dir = (
        version_dir
        / "rollback_safety"
    )

    safety_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    current_hash = calculate_file_hash(
        target_file
    )

    safety_backup = (
        safety_dir
        / (
            f"{target_file.stem}_"
            f"before_rollback_"
            f"{timestamp}_"
            f"{current_hash[:12]}"
            f"{target_file.suffix}"
        )
    )

    shutil.copy2(
        str(target_file),
        str(safety_backup)
    )

    shutil.copy2(
        str(backup_path),
        str(target_file)
    )

    restored_quality = run_quality_checks(
        target_file
    )

    if not restored_quality["passed"]:

        shutil.copy2(
            str(safety_backup),
            str(target_file)
        )

        return {
            "success": False,
            "file": file_name,
            "backup": str(backup_path),
            "reason": (
                "Restored version failed quality checks: "
                + "; ".join(
                    restored_quality["failures"]
                )
            )
        }

    restored_hash = calculate_file_hash(
        target_file
    )

    backup_hash = calculate_file_hash(
        backup_path
    )

    if restored_hash != backup_hash:

        shutil.copy2(
            str(safety_backup),
            str(target_file)
        )

        return {
            "success": False,
            "file": file_name,
            "backup": str(backup_path),
            "reason": "Rollback hash verification failed."
        }

    state = load_state()

    state[file_name] = {
        "hash": restored_hash,
        "size": target_file.stat().st_size,
        "modified_time": datetime.fromtimestamp(
            target_file.stat().st_mtime
        ).isoformat()
    }

    save_state(
        state
    )

    save_known_good_version(
        target_file
    )

    metadata, metadata_error = parse_metadata(
        target_file
    )

    if metadata_error:
        metadata = {}

    return {
        "success": True,
        "file": file_name,
        "backup": str(backup_path),
        "restored_version": metadata.get(
            "version"
        ),
        "restored_hash": restored_hash,
        "safety_backup": str(
            safety_backup
        )
    }


# ==================================================
# Run Regression Protection
# ==================================================

def run_regression_protection():

    report = run_all_regression_tests()

    if report["failed"] > 0:

        return {
            "passed": False,
            "report": report,
            "reason": (
                "Knowledge-base regression detected. "
                "Update must not be activated."
            )
        }

    return {
        "passed": True,
        "report": report,
        "reason": "All regression tests passed."
    }


# ==================================================
# Scan Knowledge Base
# ==================================================

def scan_knowledge_base():

    KNOWLEDGE_BASE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    previous_state = load_state()

    current_state = {}

    new_files = []
    modified_files = []
    unchanged_files = []
    duplicate_files = []
    invalid_files = []
    quality_failures = []
    regression_failures = []
    version_backups = []

    hash_to_file = {}

    # ----------------------------------------------
    # Scan TXT files
    # ----------------------------------------------

    for file_path in sorted(
        KNOWLEDGE_BASE_DIR.glob("*.txt")
    ):

        file_name = file_path.name

        # ------------------------------------------
        # Basic validation
        # ------------------------------------------

        valid, reason = validate_document(
            file_path
        )

        if not valid:

            quarantine_result = quarantine_file(
                file_path,
                reason
            )

            invalid_files.append(
                quarantine_result
            )

            continue

        # ------------------------------------------
        # Quality gate
        # ------------------------------------------

        quality_result = run_quality_checks(
            file_path
        )

        if not quality_result["passed"]:

            reason = (
                "Quality gate failed: "
                + "; ".join(
                    quality_result["failures"]
                )
            )

            quarantine_result = quarantine_file(
                file_path,
                reason
            )

            quality_failures.append(
                quarantine_result
            )

            continue

        # ------------------------------------------
        # Calculate hash
        # ------------------------------------------

        file_hash = calculate_file_hash(
            file_path
        )

        # ------------------------------------------
        # Check previous state
        # ------------------------------------------

        is_new = file_name not in previous_state

        old_hash = None

        if not is_new:

            old_hash = previous_state[
                file_name
            ].get("hash")

        # ------------------------------------------
        # Unchanged
        # ------------------------------------------

        if not is_new and old_hash == file_hash:

            unchanged_files.append(
                file_name
            )

        # ------------------------------------------
        # Modified
        # ------------------------------------------

        elif not is_new:

            # --------------------------------------
            # Save previous version first
            # --------------------------------------

            backup_path = backup_previous_version(
                file_path,
                old_hash
            )

            # --------------------------------------
            # Run regression protection
            # --------------------------------------

            regression_result = (
                run_regression_protection()
            )

            if not regression_result["passed"]:

                reason = (
                    "Regression gate failed. "
                    "Previous known-good version "
                    "remains active."
                )

                quarantine_result = quarantine_file(
                    file_path,
                    reason
                )

                regression_failures.append({
                    **quarantine_result,
                    "regression_report": (
                        regression_result["report"]
                    ),
                    "backup": str(
                        backup_path
                    )
                })

                # Important:
                # Do not update current state with
                # the rejected version.

                continue

            # --------------------------------------
            # Update accepted version
            # --------------------------------------

            modified_files.append(
                file_name
            )

            version_backups.append({
                "file": file_name,
                "backup": str(
                    backup_path
                )
            })

            current_state[file_name] = {
                "hash": file_hash,
                "size": file_path.stat().st_size,
                "modified_time": datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).isoformat()
            }

            save_known_good_version(
                file_path
            )

        # ------------------------------------------
        # New file
        # ------------------------------------------

        else:

            new_files.append(
                file_name
            )

            current_state[file_name] = {
                "hash": file_hash,
                "size": file_path.stat().st_size,
                "modified_time": datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).isoformat()
            }

            save_known_good_version(
                file_path
            )

        # ------------------------------------------
        # Ensure unchanged state is retained
        # ------------------------------------------

        if file_name not in current_state:

            current_state[file_name] = {
                "hash": file_hash,
                "size": file_path.stat().st_size,
                "modified_time": datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).isoformat()
            }

        # ------------------------------------------
        # Duplicate detection
        # ------------------------------------------

        if file_hash in hash_to_file:

            duplicate_files.append({
                "file": file_name,
                "duplicate_of": (
                    hash_to_file[file_hash]
                ),
                "hash": file_hash
            })

        else:

            hash_to_file[file_hash] = file_name

    # ----------------------------------------------
    # Save state
    # ----------------------------------------------

    save_state(
        current_state
    )

    return {
        "new_files": new_files,
        "modified_files": modified_files,
        "unchanged_files": unchanged_files,
        "duplicate_files": duplicate_files,
        "invalid_files": invalid_files,
        "quality_failures": quality_failures,
        "regression_failures": regression_failures,
        "version_backups": version_backups,
        "total_files": len(current_state)
    }


# ==================================================
# Print Pipeline Report
# ==================================================

def print_report(report):
    report = mask_sensitive_dict(report)

    print("\n")
    print("=" * 60)
    print("KNOWLEDGE BASE PIPELINE REPORT")
    print("=" * 60)

    print(
        f"\nTotal valid files: "
        f"{report['total_files']}"
    )

    print("\nNew files:")

    if report["new_files"]:

        for file_name in report["new_files"]:

            print(
                f"  + {file_name}"
            )

    else:

        print("  None")

    print("\nModified files:")

    if report["modified_files"]:

        for file_name in report["modified_files"]:

            print(
                f"  * {file_name}"
            )

    else:

        print("  None")

    print("\nUnchanged files:")

    if report["unchanged_files"]:

        for file_name in report["unchanged_files"]:

            print(
                f"  = {file_name}"
            )

    else:

        print("  None")

    print("\nDuplicate files:")

    if report["duplicate_files"]:

        for duplicate in report["duplicate_files"]:

            print(
                f"  ! {duplicate['file']} "
                f"is duplicate of "
                f"{duplicate['duplicate_of']}"
            )

    else:

        print("  None")

    print("\nInvalid files:")

    if report["invalid_files"]:

        for invalid in report["invalid_files"]:

            print(
                f"  X {invalid['file']}"
            )

            print(
                f"    Reason: "
                f"{invalid['reason']}"
            )

            print(
                f"    Quarantined at: "
                f"{invalid['quarantine_path']}"
            )

    else:

        print("  None")

    print("\nQuality gate failures:")

    if report["quality_failures"]:

        for failure in report["quality_failures"]:

            print(
                f"  X {failure['file']}"
            )

            print(
                f"    Reason: "
                f"{failure['reason']}"
            )

            print(
                f"    Quarantined at: "
                f"{failure['quarantine_path']}"
            )

    else:

        print("  None")

    print("\nRegression gate failures:")

    if report["regression_failures"]:

        for failure in report["regression_failures"]:

            print(
                f"  X {failure['file']}"
            )

            print(
                f"    Reason: "
                f"{failure['reason']}"
            )

            print(
                f"    Quarantined at: "
                f"{failure['quarantine_path']}"
            )

            print(
                f"    Previous backup: "
                f"{failure['backup']}"
            )

            regression_report = (
                failure["regression_report"]
            )

            print(
                f"    Regression pass rate: "
                f"{regression_report['pass_rate']}%"
            )

    else:

        print("  None")

    print("\nVersion backups:")

    if report["version_backups"]:

        for backup in report["version_backups"]:

            print(
                f"  B {backup['file']}"
            )

            print(
                f"    Backup: "
                f"{backup['backup']}"
            )

    else:

        print("  None")

    print("\n" + "=" * 60)


# ==================================================
# Print Rollback Report
# ==================================================

def print_rollback_report(result):

    result = mask_sensitive_dict(result)
    
    print("\n")
    print("=" * 60)
    print("KNOWLEDGE BASE ROLLBACK REPORT")
    print("=" * 60)

    print(
        f"\nFile: "
        f"{result.get('file')}"
    )

    if result.get("success"):

        print(
            "\nRollback status: SUCCESS"
        )

        print(
            f"Restored version: "
            f"{result.get('restored_version')}"
        )

        print(
            f"Restored hash: "
            f"{result.get('restored_hash')}"
        )

        print(
            f"Backup used: "
            f"{result.get('backup')}"
        )

        print(
            f"Safety backup: "
            f"{result.get('safety_backup')}"
        )

    else:

        print(
            "\nRollback status: FAILED"
        )

        print(
            f"Reason: "
            f"{result.get('reason')}"
        )

        if result.get("backup"):

            print(
                f"Backup: "
                f"{result.get('backup')}"
            )

    print("\n" + "=" * 60)


# ==================================================
# Retry State
# ==================================================

def load_retry_state():

    if not RETRY_STATE_FILE.exists():
        return {}

    try:

        with open(
            RETRY_STATE_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except Exception:
        return {}


def save_retry_state(state):

    KNOWLEDGE_BASE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        RETRY_STATE_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            state,
            file,
            indent=4
        )


def clear_retry_state():

    if RETRY_STATE_FILE.exists():
        RETRY_STATE_FILE.unlink()


# ==================================================
# Retry Pipeline
# ==================================================

def run_pipeline_with_retry(current_time=None):
    """
    Run the KB pipeline and maintain retry state.

    Retry intervals are 15, 30, and 60 minutes.
    The function does not sleep; the scheduler calls it
    again later and the stored failure time determines
    whether the next retry is due.
    """

    retry_state = load_retry_state()

    if not retry_state:

        report = scan_knowledge_base()

        has_failure = (
            bool(report["invalid_files"])
            or bool(report["quality_failures"])
            or bool(report["regression_failures"])
        )

        if not has_failure:
            clear_retry_state()
            return {
                "status": "success",
                "attempt": 0,
                "retry": None,
                "report": report
            }

        failed_at = datetime.now()

        retry_state = {
            "failed_at": failed_at.isoformat(
                timespec="seconds"
            ),
            "completed_attempts": 0
        }

        save_retry_state(retry_state)

        retry_status = get_retry_status(
            failed_at,
            0,
            current_time
        )

        return {
            "status": "retry_waiting",
            "attempt": 0,
            "retry": retry_status,
            "report": report
        }

    failed_at = datetime.fromisoformat(
        retry_state["failed_at"]
    )

    completed_attempts = retry_state.get(
        "completed_attempts",
        0
    )

    retry_status = get_retry_status(
        failed_at,
        completed_attempts,
        current_time
    )

    if not retry_status["retry_due"]:
        return {
            "status": "retry_waiting",
            "attempt": completed_attempts,
            "retry": retry_status,
            "report": None
        }

    retry_attempt = completed_attempts + 1

    print("\n")
    print("=" * 60)
    print("KNOWLEDGE BASE RETRY")
    print("=" * 60)
    print(f"\nRetry attempt: {retry_attempt}")
    print(
        f"Scheduled delay: "
        f"{retry_status['next_retry']['delay_minutes']} minutes"
    )

    report = scan_knowledge_base()

    has_failure = (
        bool(report["invalid_files"])
        or bool(report["quality_failures"])
        or bool(report["regression_failures"])
    )

    if not has_failure:
        clear_retry_state()

        print("\nRetry status: SUCCESS")
        print("Pipeline completed successfully.")

        return {
            "status": "success",
            "attempt": retry_attempt,
            "retry": None,
            "report": report
        }

    retry_state["completed_attempts"] = retry_attempt
    save_retry_state(retry_state)

    next_retry = get_retry_status(
        failed_at,
        retry_attempt,
        current_time
    )

    if not next_retry["retry_available"]:
        clear_retry_state()

        print("\nRetry status: FINAL FAILURE")
        print("Maximum retry attempts reached.")

        return {
            "status": "final_failure",
            "attempt": retry_attempt,
            "retry": next_retry,
            "report": report
        }

    print("\nRetry status: FAILED")
    print(
        "Next retry:",
        next_retry["next_retry"]["retry_time"]
    )

    return {
        "status": "retry_waiting",
        "attempt": retry_attempt,
        "retry": next_retry,
        "report": report
    }


# ==================================================
# Health Failure / Automatic Rollback
# ==================================================

def load_health_state():
    if not HEALTH_STATE_FILE.exists():
        return {}
    try:
        with open(HEALTH_STATE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def save_health_state(state):
    KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
    with open(HEALTH_STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(state, file, indent=4)


def clear_health_state():
    if HEALTH_STATE_FILE.exists():
        HEALTH_STATE_FILE.unlink()


def run_health_check(file_names=None):
    """Check only the files that were activated by the latest successful run."""
    if file_names is None:
        file_names = []

    failures = []
    checked_files = []

    for file_name in file_names:
        file_path = KNOWLEDGE_BASE_DIR / file_name
        checked_files.append(file_name)
        if not file_path.exists():
            failures.append({
                "file": file_name,
                "reason": "Activated file is missing."
            })
            continue

        quality_result = run_quality_checks(file_path)
        if not quality_result["passed"]:
            failures.append({
                "file": file_name,
                "reason": "; ".join(quality_result["failures"])
            })

    regression_result = None
    if file_names and not failures:
        regression_result = run_regression_protection()
        if not regression_result["passed"]:
            failures.append({
                "file": "regression_suite",
                "reason": "; ".join(regression_result["report"].get("failed_tests", []))
                    if isinstance(regression_result.get("report"), dict)
                    else regression_result["reason"]
            })

    return {
        "healthy": len(failures) == 0,
        "checked_files": checked_files,
        "failures": failures,
        "regression": regression_result
    }


def normalize_activated_files(activated_files):
    """Accept only explicitly tracked KB activation records."""
    if not isinstance(activated_files, list):
        return []

    normalized = []
    for item in activated_files:
        if isinstance(item, dict):
            file_name = item.get("file")
            activation_type = item.get("type", "modified")
        else:
            file_name = item
            activation_type = "modified"

        if not isinstance(file_name, str):
            continue

        file_path = KNOWLEDGE_BASE_DIR / file_name
        if file_path.suffix.lower() != ".txt":
            continue

        normalized.append({
            "file": file_name,
            "type": activation_type
        })

    return normalized



def monitor_health(current_time=None, activated_files=None, health_check_result=None):
    """Track continuous health failure and rollback after five minutes."""
    if current_time is None:
        current_time = datetime.now()

    state = load_health_state()

    explicit_activated_files = normalize_activated_files(activated_files)

    if not state and explicit_activated_files:
        state = {
            "activated_files": explicit_activated_files,
            "activated_at": current_time.isoformat(timespec="seconds")
        }

    tracked_files = normalize_activated_files(
        state.get("activated_files", [])
    )

    if not tracked_files:
        clear_health_state()
        return {
            "status": "not_applicable",
            "healthy": True,
            "message": "No newly activated files require post-activation health monitoring.",
            "rollback": []
        }

    if health_check_result is None:
        health_check_result = run_health_check(tracked_files)

    if health_check_result.get("healthy"):
        clear_health_state()
        return {
            "status": "healthy",
            "healthy": True,
            "message": "Post-activation health check passed.",
            "rollback": []
        }

    failed_at_text = state.get("failed_at")
    if not failed_at_text:
        state["failed_at"] = current_time.isoformat(timespec="seconds")
        state["last_failure"] = health_check_result.get("failures", [])
        state["activated_files"] = tracked_files
        save_health_state(state)
        return {
            "status": "unhealthy_waiting",
            "healthy": False,
            "elapsed_minutes": 0,
            "message": "Health failure detected; five-minute rollback timer started.",
            "failures": health_check_result.get("failures", []),
            "rollback": []
        }

    failed_at = datetime.fromisoformat(failed_at_text)
    elapsed_seconds = max(0, (current_time - failed_at).total_seconds())
    elapsed_minutes = elapsed_seconds / 60
    state["last_failure"] = health_check_result.get("failures", [])

    if elapsed_minutes < HEALTH_FAILURE_LIMIT_MINUTES:
        save_health_state(state)
        return {
            "status": "unhealthy_waiting",
            "healthy": False,
            "elapsed_minutes": round(elapsed_minutes, 2),
            "message": "Health remains unhealthy; rollback threshold has not been reached.",
            "failures": health_check_result.get("failures", []),
            "rollback": []
        }

    rollback_results = []
    for item in tracked_files:
        file_name = item.get("file") if isinstance(item, dict) else item
        activation_type = item.get("type", "modified") if isinstance(item, dict) else "modified"

        if activation_type == "new":
            target_file = KNOWLEDGE_BASE_DIR / file_name
            if target_file.exists():
                try:
                    target_file.unlink()
                    rollback_results.append({
                        "success": True,
                        "file": file_name,
                        "action": "removed_new_file"
                    })
                except Exception as error:
                    rollback_results.append({
                        "success": False,
                        "file": file_name,
                        "reason": f"Could not remove newly activated file: {error}"
                    })
            else:
                rollback_results.append({
                    "success": True,
                    "file": file_name,
                    "action": "new_file_already_absent"
                })
        else:
            rollback_results.append(
    rollback_file(file_name, role="system")
)
    rollback_success = all(item.get("success") for item in rollback_results)

    if not rollback_success:
        save_health_state(state)
        return {
            "status": "rollback_failed",
            "healthy": False,
            "elapsed_minutes": round(elapsed_minutes, 2),
            "message": "Health failure exceeded five minutes, but automatic rollback did not fully succeed.",
            "failures": health_check_result.get("failures", []),
            "rollback": rollback_results
        }

    restored_health = run_health_check(
        [item.get("file") for item in tracked_files
         if item.get("type", "modified") != "new"]
    )
    clear_health_state()

    return {
        "status": "rolled_back" if restored_health["healthy"] else "rollback_failed_health_check",
        "healthy": restored_health["healthy"],
        "elapsed_minutes": round(elapsed_minutes, 2),
        "message": (
            "Automatic rollback completed and restored version passed health checks."
            if restored_health["healthy"]
            else "Automatic rollback completed, but restored version failed health checks."
        ),
        "failures": health_check_result.get("failures", []),
        "rollback": rollback_results,
        "restored_health": restored_health
    }


# ==================================================
# Scheduled Pipeline Runner
# ==================================================

def run_scheduled_pipeline(current_time=None, role=None):
    """
    Run the KB pipeline only when the configured
    schedule and maintenance window allow it.

    Failed pipeline runs use the configured
    15 / 30 / 60 minute retry schedule.
    """
    if role is None:
        role = get_current_role()

    check_permission("kb_schedule", role)
    monitoring_start = start_timer()
    schedule_result = can_run_pipeline(
        current_time
    )

    print("\n")
    print("=" * 60)
    print("KNOWLEDGE BASE SCHEDULE CHECK")
    print("=" * 60)

    configuration = get_schedule_configuration()

    print(
        "\nConfigured schedule:",
        configuration["schedule_start"],
        "to",
        configuration["schedule_end"]
    )

    print(
        "Maintenance window:",
        configuration["maintenance_start"],
        "to",
        configuration["maintenance_end"]
    )

    if not schedule_result["allowed"]:

        print("\nPipeline status: BLOCKED")
        print("Reason:", schedule_result["reason"])
        print("=" * 60)

        return None

    print("\nPipeline status: ALLOWED")
    print("Reason:", schedule_result["reason"])
    print("=" * 60)

    result = run_pipeline_with_retry(
        current_time=current_time
    )
    monitoring_latency = calculate_latency(
        monitoring_start
    )
    if result["report"] is not None:
        print_report(
            result["report"]
        )

    if result.get("status") == "success" and result.get("report") is not None:
        activated_files = (
            [{"file": name, "type": "modified"} for name in result["report"].get("modified_files", [])]
            + [{"file": name, "type": "new"} for name in result["report"].get("new_files", [])]
        )
        health_result = monitor_health(
            current_time=current_time,
            activated_files=activated_files
        )
        result["health"] = health_result
        print("\nPost-activation health status:", health_result["status"])
        if health_result.get("rollback"):
            for rollback_result in health_result["rollback"]:
                print_rollback_report(rollback_result)
    pipeline_failures = []

    if result.get("report"):
        report = result["report"]

        pipeline_failures.extend(
            report.get("invalid_files", [])
        )

        pipeline_failures.extend(
            report.get("quality_failures", [])
        )

        pipeline_failures.extend(
            report.get("regression_failures", [])
        )

    health_status = None

    if result.get("health"):
        health_status = result["health"].get(
            "status"
        )

    monitoring_record = record_pipeline_run(
        status=result.get("status", "unknown"),
        latency_seconds=monitoring_latency,
        failures=pipeline_failures,
        confidence=None,
        escalations=0,
        health_status=health_status
    )

    result["monitoring"] = monitoring_record

    alerts = generate_monitoring_alerts(
        latency_seconds=monitoring_latency,
        failures=pipeline_failures,
        confidence=None,
        escalations=0,
        health_status=health_status
    )

    result["monitoring_alerts"] = alerts
    return result


# ==================================================
# Main
# ==================================================

if __name__ == "__main__":

    run_scheduled_pipeline()