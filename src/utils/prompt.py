def get_questions_from_content_prompt_mistral(context, nbr_questions=40, language="english"):
        return f"""<s><<SYS>>
You are a highly detailed-oriented Assistant.
Your task is to generate unique and context-specific questions based on the provided text. These questions should be designed to explore every aspect of the context in depth.
Guidelines for question formulation:
1. Each question must directly relate to the information in the context.
2. Avoid general or vague questions. Instead, tailor each question to specific details, names, events, or facts mentioned in the context.
3. Ensure that the questions collectively cover all key elements of the context, including but not limited to names, dates, events, personal information, statistics, and any specific terminologies or concepts mentioned.
4. Do not provide answers to these questions.
5. The question should always include "What", "Who", "When", "Where" when possible.


Examples of well-formulated questions:
- Instead of "What is the birth date of the person?", ask "What is the birth date of [person's name] mentioned in the [describe the context]?"
- Instead of "What is the email?", ask "What is the email of [person's name] mentioned in the [describe the context]?"
- Instead of "What are the skills?", ask "What are the skills of [person's name] mentioned in the [describe the context]?"
- Instead of "What are the expertise?", ask "What are the expertise of [person's name] mentioned in the [describe the context]?"
- Instead of "What are the programming languages?", ask "what are the programming languages that [person's name] can use?"
- Instead of "What are the qualities?", ask "What are the qualities of [person's name] mentioned in the [describe the context]?"
- Replace "What is the system used?" with "What specific system is mentioned as being used in [describe the context]?"
- Instead of "What is the name of the person?", ask "Who is the person referred to as [specific role or description] in the [describe the context]?"
- Change "What is the end date of the project?" to "What is the projected completion date for [project name] as described in the [describe the context]?"
</s><</SYS>>

Context:
```
{context}
```

User : Based on the above context, please generate a list of exactly {nbr_questions} distinct and contextually relevant questions. Ensure that these questions comprehensively cover the provided context.
Don't never never ask general or vague questions.
Always add "What", "Who", "When", "Where" when possible.
Do not end the question with phrase like "in the context" or "in the given context" or "dans le contexte" or similar.
Give a list of exactly {nbr_questions} questions.
Give me the questions in {language} language.
Assistant: """


def get_answer_from_content_prompt_mistral(context, question, language="english"):
        print("question", question)
        return f"""<s><<SYS>>
You are a highly detail-oriented Assistant tasked with generating professional and detailed answers. Your responses should be based strictly on the provided context and in the specified language. Do not use external knowledge or information not included in the context.
</s><</SYS>>

Context:

{context}


User: Please answer the following question in {language}: "{question}".
If the context does not provide enough information, respond with: "I do not have enough content to answer this question."

[Reminder: The response must be in {language}.]

Assistant: """


def get_questions_from_content(context, nbr_questions=30, model="mistral", language="english"):
        return get_questions_from_content_prompt_mistral(context, nbr_questions, language)


def get_answer_question_from_content(context, question, model="mistral"):
        return get_answer_from_content_prompt_mistral(context, question, language="english")
