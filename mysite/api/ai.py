
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

todos_router = APIRouter()

model = ChatOllama(
    model="llama3.2:latest",
    temperature=0,
    format="json"
)


# ---------- Schemas ----------

class MeetingAnalyzeSchema(BaseModel):
    text: str = Field(min_length=1)


class MeetingTaskSchema(BaseModel):
    title: str
    assignee: str | None = None
    deadline_text: str | None = None


class MeetingAnalyzeResponse(BaseModel):
    tasks: list[MeetingTaskSchema]


class TaskCheckSchema(BaseModel):
    task_number: int
    needs_clarification: bool
    missing_fields: list[str]


class TaskStatsSchema(BaseModel):
    total_tasks: int
    complete_tasks: int
    without_assignee: int
    without_deadline: int


class MeetingCheckResponse(BaseModel):
    stats: TaskStatsSchema
    checks: list[TaskCheckSchema]


class PlanCreateSchema(BaseModel):
    goal: str = Field(min_length=1)
    constraints: str = ""
    count_tasks: int = Field(ge=1, le=30)


class TaskResponseSchema(BaseModel):
    task_number: int
    title: str
    details: str
    priority: int = Field(ge=1, le=3)
    status: Literal["todo"] = "todo"


class PlanResponseSchema(BaseModel):
    plan_status: Literal["draft"] = "draft"
    tasks: list[TaskResponseSchema]
    tasks_count: int


# ---------- Prompts ----------

analyze_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        Ты Meeting Analyzer.
        Извлекай только согласованные задачи из текста совещания.
        Не придумывай исполнителей и сроки.
        Если исполнитель неизвестен, используй null.
        Если срок неизвестен, используй null.
        Не дублируй задачи.
        Сохраняй порядок задач.
        Возвращай JSON с полем tasks.
        """
    ),
    ("human", "Текст совещания: {text}")
])


plan_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        Ты AI Task Planner.
        Создай ровно count_tasks задач.
        Учитывай цель и ограничения.
        Не дублируй задачи.
        Расположи задачи в логическом порядке.
        Каждая задача должна иметь title и details.
        priority: 1 — низкий, 2 — средний, 3 — высокий.
        task_number начинается с 1.
        status всегда todo.
        plan_status всегда draft.
        tasks_count равен количеству задач.
        Верни только JSON.
        """
    ),
    (
        "human",
        """
        Цель: {goal}
        Ограничения: {constraints}
        Количество задач: {count_tasks}
        """
    )
])


analyze_chain = analyze_prompt | model.with_structured_output(
    MeetingAnalyzeResponse
)

plan_chain = plan_prompt | model.with_structured_output(
    PlanResponseSchema
)


# ---------- Analyze meeting ----------

@todos_router.post(
    "/meetings/analyze/",
    response_model=list[MeetingTaskSchema]
)
async def meeting_analyze(data: MeetingAnalyzeSchema):
    try:
        result = await analyze_chain.ainvoke({
            "text": data.text
        })
        return result.tasks

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Ошибка анализа совещания: {str(error)}"
        )


# ---------- Check tasks ----------

@todos_router.post(
    "/meetings/check_tasks/",
    response_model=MeetingCheckResponse
)
async def meeting_check_tasks(tasks: list[MeetingTaskSchema]):
    checks = []
    complete_tasks = 0
    without_assignee = 0
    without_deadline = 0

    for index, task in enumerate(tasks, start=1):
        missing_fields = []

        if not task.assignee:
            missing_fields.append("assignee")
            without_assignee += 1

        if not task.deadline_text:
            missing_fields.append("deadline_text")
            without_deadline += 1

        needs_clarification = bool(missing_fields)

        if not needs_clarification:
            complete_tasks += 1

        checks.append(
            TaskCheckSchema(
                task_number=index,
                needs_clarification=needs_clarification,
                missing_fields=missing_fields
            )
        )

    return MeetingCheckResponse(
        stats=TaskStatsSchema(
            total_tasks=len(tasks),
            complete_tasks=complete_tasks,
            without_assignee=without_assignee,
            without_deadline=without_deadline
        ),
        checks=checks
    )


# ---------- Create task plan ----------

@todos_router.post(
    "/plans/create/",
    response_model=PlanResponseSchema
)
async def create_plan(data: PlanCreateSchema):
    try:
        result = await plan_chain.ainvoke({
            "goal": data.goal,
            "constraints": data.constraints,
            "count_tasks": data.count_tasks
        })

        # Текшерүү: тапшырмалардын саны суралган санга барабар болушу керек.
        if len(result.tasks) != data.count_tasks:
            raise HTTPException(
                status_code=502,
                detail="AI вернул неправильное количество задач"
            )

        return result

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Ошибка создания плана: {str(error)}"
        )
