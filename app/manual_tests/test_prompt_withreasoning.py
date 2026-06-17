from src.llm.prompts import build_prompt

def main():
    question = "Why is gold moving higher?"

    evidence = [
        "Article 1: Inflation concerns are rising.",
        "Article 2: Markets expect lower rates."
    ]

    driver_summary = """Driver Reasoning Summary:
- inflation (1) -> gold: supportive, silver: supportive
- rates (1) -> gold: negative, silver: negative

Gold signals: supportive, negative
Silver signals: supportive, negative
"""

    system_prompt, user_prompt = build_prompt(question, evidence, driver_summary)

    print("SYSTEM PROMPT:")
    print(system_prompt)
    print("\nUSER PROMPT:")
    print(user_prompt)

if __name__ == "__main__":
    main()