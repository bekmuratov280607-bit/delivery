from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from mysite.database.schema import PlanResponseSchema


model = ChatOllama(
    model="llama3.2:latest",
    temperature=0,
    format="json"
)


prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        Ты AI Task Planner.

        Твоя задача — преобразовать цель пользователя
        в структурированный план выполнения.

        Правила:

        1. Создай ровно count_tasks задач.
        2. Учитывай все ограничения constraints.
        3. Каждая задача должна быть конкретной.
        4. Не дублируй задачи.
        5. Расположи задачи в логическом порядке.
        6. Учитывай зависимости между задачами.
        7. Не пропускай важные части основной цели.
        8. Не добавляй запрещённые технологии или действия.
        9. Назначь каждой задаче priority от 1 до 3.

        Приоритет:
        1 — низкая важность.
        2 — средняя важность.
        3 — высокая важность.

        Высокая сложность не всегда означает
        высокий приоритет.

        Обязательные поля каждой задачи:
        task_number, title, details, priority, status.

        status всегда "todo".
        plan_status всегда "draft".
        tasks_count равен count_tasks.

        Верни только JSON по заданной схеме.
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


chain = prompt | model.with_structured_output(
    PlanResponseSchema
)


async def create_ai_plan(goal: str, constraints: str, count_tasks: int):

    result = await chain.ainvoke({
        "goal": goal,
        "constraints": constraints,
        "count_tasks": count_tasks
    })

    if len(result.tasks) != count_tasks:
        raise ValueError(
            "AI вернул неправильное количество задач"
        )

    for index, task in enumerate(result.tasks, start=1):
        task.task_number = index
        task.status = "todo"

    result.plan_status = "draft"
    result.tasks_count = len(result.tasks)

    return result