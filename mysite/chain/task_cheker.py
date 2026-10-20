def check_meeting_tasks(tasks):

    checks = []
    complete_tasks = 0
    without_assignee = 0
    without_deadline = 0

    for index, task in enumerate(tasks, start=1):

        missing_fields = []

        if not task.assignee or not task.assignee.strip():
            missing_fields.append("assignee")
            without_assignee += 1

        if not task.deadline_text or not task.deadline_text.strip():
            missing_fields.append("deadline_text")
            without_deadline += 1

        if not missing_fields:
            complete_tasks += 1

        checks.append({
            "task_number": index,
            "needs_clarification": bool(missing_fields),
            "missing_fields": missing_fields
        })

    return {
        "stats": {
            "total_tasks": len(tasks),
            "complete_tasks": complete_tasks,
            "without_assignee": without_assignee,
            "without_deadline": without_deadline
        },
        "checks": checks
    }