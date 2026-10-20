from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from mysite.database.schema import MeetingAnalyzeResponse


model = ChatOllama(
    model="llama3.2:latest",
    temperature=0,
    format="json"
)


analyze_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        Ты Meeting Analyzer.

        Извлекай из текста совещания только реальные задачи.

        Правила:
        1. Включай согласованные поручения.
        2. Игнорируй идеи без принятого решения.
        3. Не придумывай исполнителей.
        4. Не придумывай сроки.
        5. Если исполнитель неизвестен, используй null.
        6. Если срок неизвестен, используй null.
        7. Сохраняй исходную формулировку срока.
        8. Не создавай дублирующиеся задачи.
        9. Сохраняй порядок задач.

        Возвращай JSON с полем tasks,
        содержащим массив объектов:
        title, assignee, deadline_text.
        """
    ),
    (
        "human",
        "Текст совещания: {text}"
    )
])


analyze_chain = analyze_prompt | model.with_structured_output(
    MeetingAnalyzeResponse
)


async def analyze_meeting(text: str):

    result = await analyze_chain.ainvoke({
        "text": text
    })

    return result.tasks