from datetime import datetime, timedelta, time





# ==================================================

# Configuration

# ==================================================



BUSINESS_START = time(9, 0)

BUSINESS_END = time(18, 0)



SLA_HOURS = {

    "critical": 2,

    "high": 4,

    "medium": 8,

    "low": 24,

}



DEFAULT_HOLIDAYS = {

    "2026-01-26",

    "2026-08-15",

    "2026-10-02",

}





# ==================================================

# Agent Configuration

# ==================================================



AGENTS = [

    {

        "agent_id": "AG001",

        "name": "Support Agent 1",

        "skills": [

            "delivery_delay",

            "general_support_issue",

        ],

        "available": True,

        "workload": 2,

    },

    {

        "agent_id": "AG002",

        "name": "Payment Agent",

        "skills": [

            "payment_issue",

            "refund_issue",

        ],

        "available": True,

        "workload": 1,

    },

    {

        "agent_id": "AG003",

        "name": "Returns Agent",

        "skills": [

            "return_request",

            "damaged_product",

            "wrong_product",

        ],

        "available": True,

        "workload": 3,

    },

    {

        "agent_id": "AG004",

        "name": "Technical Support Agent",

        "skills": [

            "product_not_working",

            "general_support_issue",

        ],

        "available": True,

        "workload": 2,

    },

]





# ==================================================

# Business Day Helpers

# ==================================================



def is_holiday(

    current_datetime,

    holidays=None,

):

    if holidays is None:

        holidays = DEFAULT_HOLIDAYS



    date_string = current_datetime.strftime(

        "%Y-%m-%d"

    )



    return date_string in holidays





def is_business_day(

    current_datetime,

    holidays=None,

):

    if holidays is None:

        holidays = DEFAULT_HOLIDAYS



    if current_datetime.weekday() >= 5:

        return False



    if is_holiday(

        current_datetime,

        holidays,

    ):

        return False



    return True





def is_business_hours(

    current_datetime,

):

    current_time = current_datetime.time()



    return (

        BUSINESS_START

        <= current_time

        <= BUSINESS_END

    )





# ==================================================

# Move To Business Time

# ==================================================



def move_to_business_time(

    current_datetime,

    holidays=None,

):

    if holidays is None:

        holidays = DEFAULT_HOLIDAYS



    current = current_datetime



    while True:



        if not is_business_day(

            current,

            holidays,

        ):

            current = (

                current

                + timedelta(days=1)

            ).replace(

                hour=BUSINESS_START.hour,

                minute=BUSINESS_START.minute,

                second=0,

                microsecond=0,

            )

            continue



        current_time = current.time()



        if current_time < BUSINESS_START:

            return current.replace(

                hour=BUSINESS_START.hour,

                minute=BUSINESS_START.minute,

                second=0,

                microsecond=0,

            )



        if current_time > BUSINESS_END:

            current = (

                current

                + timedelta(days=1)

            ).replace(

                hour=BUSINESS_START.hour,

                minute=BUSINESS_START.minute,

                second=0,

                microsecond=0,

            )

            continue



        return current





# ==================================================

# Add Business Hours

# ==================================================



def add_business_hours(

    start_datetime,

    hours,

    holidays=None,

):

    if holidays is None:

        holidays = DEFAULT_HOLIDAYS



    current = move_to_business_time(

        start_datetime,

        holidays,

    )



    remaining_seconds = (

        hours * 60 * 60

    )



    while remaining_seconds > 0:



        current = move_to_business_time(

            current,

            holidays,

        )



        end_of_business = current.replace(

            hour=BUSINESS_END.hour,

            minute=BUSINESS_END.minute,

            second=0,

            microsecond=0,

        )



        available_seconds = (

            end_of_business - current

        ).total_seconds()



        if remaining_seconds <= available_seconds:

            return current + timedelta(

                seconds=remaining_seconds

            )



        remaining_seconds -= (

            available_seconds

        )



        current = (

            current

            + timedelta(days=1)

        ).replace(

            hour=BUSINESS_START.hour,

            minute=BUSINESS_START.minute,

            second=0,

            microsecond=0,

        )



    return current





# ==================================================

# Priority Calculation

# ==================================================



def calculate_priority(

    issue,

    sentiment="neutral",

    severity="medium",

    waiting_minutes=0,

    business_impact="normal",

):

    score = 0



    severity_scores = {

        "critical": 6,

        "high": 4,

        "medium": 2,

        "low": 1,

    }



    score += severity_scores.get(

        severity.lower(),

        2,

    )



    sentiment_scores = {

        "urgent": 4,

        "frustrated": 3,

        "negative": 2,

        "sarcastic": 2,

        "neutral": 0,

        "positive": 0,

    }



    score += sentiment_scores.get(

        sentiment.lower(),

        0,

    )



    if waiting_minutes >= 60:

        score += 3



    elif waiting_minutes >= 30:

        score += 2



    elif waiting_minutes >= 15:

        score += 1



    impact_scores = {

        "critical": 4,

        "high": 3,

        "normal": 1,

        "low": 0,

    }



    score += impact_scores.get(

        business_impact.lower(),

        1,

    )



    if score >= 10:

        return "critical"



    if score >= 7:

        return "high"



    if score >= 4:

        return "medium"



    return "low"





# ==================================================

# SLA Calculation

# ==================================================



def calculate_sla(

    priority,

    created_at=None,

    holidays=None,

):

    if created_at is None:

        created_at = datetime.now()



    priority = priority.lower()



    sla_hours = SLA_HOURS.get(

        priority,

        SLA_HOURS["medium"],

    )



    deadline = add_business_hours(

        created_at,

        sla_hours,

        holidays,

    )



    return {

        "priority": priority,

        "sla_hours": sla_hours,

        "created_at": created_at.isoformat(),

        "sla_deadline": deadline.isoformat(),

    }





# ==================================================

# SLA Progress

# ==================================================



def calculate_business_seconds(
    start_datetime,
    end_datetime,
    holidays=None,
):
    """
    Calculate elapsed time using only configured business hours.

    Weekends and configured holidays are excluded. Time before
    09:00 or after 18:00 is also excluded.
    """
    if holidays is None:
        holidays = DEFAULT_HOLIDAYS

    if end_datetime <= start_datetime:
        return 0.0

    current = start_datetime
    total_seconds = 0.0

    while current < end_datetime:
        if not is_business_day(current, holidays):
            current = (
                current + timedelta(days=1)
            ).replace(
                hour=BUSINESS_START.hour,
                minute=BUSINESS_START.minute,
                second=0,
                microsecond=0,
            )
            continue

        business_start = current.replace(
            hour=BUSINESS_START.hour,
            minute=BUSINESS_START.minute,
            second=0,
            microsecond=0,
        )

        business_end = current.replace(
            hour=BUSINESS_END.hour,
            minute=BUSINESS_END.minute,
            second=0,
            microsecond=0,
        )

        interval_start = max(
            current,
            business_start,
        )

        interval_end = min(
            end_datetime,
            business_end,
        )

        if interval_start < interval_end:
            total_seconds += (
                interval_end - interval_start
            ).total_seconds()

        if end_datetime <= business_end:
            break

        current = (
            current + timedelta(days=1)
        ).replace(
            hour=BUSINESS_START.hour,
            minute=BUSINESS_START.minute,
            second=0,
            microsecond=0,
        )

    return total_seconds


def calculate_sla_progress(
    created_at,
    sla_deadline,
    current_time=None,
):
    if current_time is None:
        current_time = datetime.now()

    if isinstance(
        created_at,
        str,
    ):
        created_at = datetime.fromisoformat(
            created_at
        )

    if isinstance(
        sla_deadline,
        str,
    ):
        sla_deadline = datetime.fromisoformat(
            sla_deadline
        )

    total_seconds = calculate_business_seconds(
        created_at,
        sla_deadline,
    )

    elapsed_seconds = calculate_business_seconds(
        created_at,
        current_time,
    )

    if total_seconds <= 0:
        progress = 100.0

    else:
        progress = (
            elapsed_seconds
            / total_seconds
        ) * 100

    progress = max(
        0.0,
        min(100.0, progress),
    )

    warning = progress >= 75.0

    breached = (
        current_time >= sla_deadline
    )

    if breached:
        status = "breached"

    elif warning:
        status = "warning"

    else:
        status = "within_sla"

    return {
        "progress_percent": round(
            progress,
            2,
        ),
        "warning": warning,
        "breached": breached,
        "status": status,
    }


def determine_sla_escalation(

    sla_progress,

):

    if sla_progress["breached"]:



        return {

            "escalation": True,

            "escalation_type":

                "sla_breach",

            "reason":

                "SLA deadline has been breached.",

            "action":

                "Escalate ticket immediately.",

        }



    if sla_progress["warning"]:



        return {

            "escalation": True,

            "escalation_type":

                "sla_warning",

            "reason":

                "Ticket has reached 75% of its SLA.",

            "action":

                "Prioritize ticket for resolution.",

        }



    return {

        "escalation": False,

        "escalation_type": None,

        "reason": None,

        "action": None,

    }





# ==================================================

# Agent Routing

# ==================================================



def route_ticket(

    issue,

    agents=None,

):

    if agents is None:

        agents = AGENTS



    eligible_agents = []



    for agent in agents:



        if not agent["available"]:

            continue



        if issue not in agent["skills"]:

            continue



        eligible_agents.append(agent)



    if not eligible_agents:



        return {

            "assigned": False,

            "agent_id": None,

            "agent_name": None,

            "reason":

                "No available agent with "

                "the required skill.",

        }



    selected_agent = min(

        eligible_agents,

        key=lambda agent: agent["workload"],

    )



    return {

        "assigned": True,

        "agent_id":

            selected_agent["agent_id"],

        "agent_name":

            selected_agent["name"],

        "reason":

            "Assigned based on required skill "

            "and lowest current workload.",

    }





# ==================================================

# Complete Ticket Priority Analysis

# ==================================================



def analyze_ticket_priority(

    ticket,

    sentiment="neutral",

    severity="medium",

    waiting_minutes=0,

    business_impact="normal",

    created_at=None,

):

    issue = ticket.get(

        "issue",

        "general_support_issue",

    )



    priority = calculate_priority(

        issue=issue,

        sentiment=sentiment,

        severity=severity,

        waiting_minutes=waiting_minutes,

        business_impact=business_impact,

    )



    sla = calculate_sla(

        priority=priority,

        created_at=created_at,

    )



    sla_progress = calculate_sla_progress(

        created_at=sla["created_at"],

        sla_deadline=sla["sla_deadline"],

    )



    escalation = determine_sla_escalation(

        sla_progress

    )



    routing = route_ticket(

        issue=issue

    )



    return {

        "ticket_id":

            ticket.get("ticket_id"),

        "issue":

            issue,

        "priority":

            priority,

        "severity":

            severity,

        "sentiment":

            sentiment,

        "waiting_minutes":

            waiting_minutes,

        "business_impact":

            business_impact,

        "sla":

            sla,

        "sla_progress":

            sla_progress,

        "sla_escalation":

            escalation,

        "routing":

            routing,

    }





# ==================================================

# SLA Warning Test

# ==================================================



def test_sla_warning():

    created_at = datetime(

        2026,

        9,

        22,

        10,

        0,

    )



    deadline = datetime(

        2026,

        9,

        22,

        14,

        0,

    )



    # 3 hours after creation = 75%

    current_time = datetime(

        2026,

        9,

        22,

        13,

        0,

    )



    result = calculate_sla_progress(

        created_at=created_at,

        sla_deadline=deadline,

        current_time=current_time,

    )



    escalation = determine_sla_escalation(

        result

    )



    print("\n--- Test 6: SLA 75% Warning ---")

    print("Progress:", result)

    print("Escalation:", escalation)



    assert result["progress_percent"] == 75.0

    assert result["warning"] is True

    assert result["breached"] is False

    assert result["status"] == "warning"

    assert escalation["escalation"] is True

    assert (

        escalation["escalation_type"]

        == "sla_warning"

    )



    print("PASS: 75% SLA warning works.")





# ==================================================

# SLA Breach Test

# ==================================================



def test_sla_breach():

    created_at = datetime(

        2026,

        9,

        22,

        10,

        0,

    )



    deadline = datetime(

        2026,

        9,

        22,

        14,

        0,

    )



    # One hour after deadline

    current_time = datetime(

        2026,

        9,

        22,

        15,

        0,

    )



    result = calculate_sla_progress(

        created_at=created_at,

        sla_deadline=deadline,

        current_time=current_time,

    )



    escalation = determine_sla_escalation(

        result

    )



    print("\n--- Test 7: SLA Breach ---")

    print("Progress:", result)

    print("Escalation:", escalation)



    assert result["progress_percent"] == 100.0

    assert result["warning"] is True

    assert result["breached"] is True

    assert result["status"] == "breached"

    assert escalation["escalation"] is True

    assert (

        escalation["escalation_type"]

        == "sla_breach"

    )



    print("PASS: SLA breach escalation works.")





# ==================================================

# Standalone Tests

# ==================================================



def test_sla_business_hours_progress():
    created_at = datetime(
        2026,
        9,
        25,
        17,
        0,
    )

    deadline = datetime(
    2026,
    9,
    28,
    17,
    0,
)

    current_time = datetime(
        2026,
        9,
        28,
        9,
        0,
    )

    result = calculate_sla_progress(
        created_at=created_at,
        sla_deadline=deadline,
        current_time=current_time,
    )

    assert abs(result["progress_percent"] - 11.11) < 0.01
    assert result["warning"] is False
    assert result["breached"] is False
    assert result["status"] == "within_sla"

    print("PASS: SLA progress excludes weekends.")


if __name__ == "__main__":



    print("\n" + "=" * 60)

    print("TASK 3 - DAY 2 TESTS")

    print("=" * 60)



    # Test 1

    print("\n--- Test 1: Critical Ticket ---")



    ticket_1 = {

        "ticket_id": "TKT-CRITICAL",

        "issue": "payment_issue",

    }



    result_1 = analyze_ticket_priority(

        ticket=ticket_1,

        sentiment="urgent",

        severity="critical",

        waiting_minutes=60,

        business_impact="critical",

    )



    print(result_1)



    # Test 2

    print("\n--- Test 2: Medium Ticket ---")



    ticket_2 = {

        "ticket_id": "TKT-MEDIUM",

        "issue": "delivery_delay",

    }



    result_2 = analyze_ticket_priority(

        ticket=ticket_2,

        sentiment="negative",

        severity="medium",

        waiting_minutes=10,

        business_impact="normal",

    )



    print(result_2)



    # Test 3

    print("\n--- Test 3: Low Ticket ---")



    ticket_3 = {

        "ticket_id": "TKT-LOW",

        "issue": "general_support_issue",

    }



    result_3 = analyze_ticket_priority(

        ticket=ticket_3,

        sentiment="neutral",

        severity="low",

        waiting_minutes=0,

        business_impact="low",

    )



    print(result_3)



    # Test 4

    print("\n--- Test 4: SLA Calculation ---")



    test_time = datetime(

        2026,

        9,

        22,

        10,

        0,

    )



    sla_result = calculate_sla(

        priority="high",

        created_at=test_time,

    )



    print(sla_result)



    # Test 5

    print("\n--- Test 5: Agent Routing ---")



    routing_result = route_ticket(

        issue="payment_issue"

    )



    print(routing_result)



    # Test 6

    test_sla_warning()



    # Test 7

    test_sla_breach()



    print("\n" + "=" * 60)

    print("ALL DAY 2 TESTS COMPLETED")

    print("=" * 60)