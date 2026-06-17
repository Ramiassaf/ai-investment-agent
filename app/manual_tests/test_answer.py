from src.llm.answer import answer_question

def main():
    # question = "How do geopolitical tensions affect gold?"
    question = "What is the outlook for silver demand?"

    print("=" * 80)
    print("QUESTION:")
    print(question)
    print("=" * 80)
    answer_question(question)


if __name__ == "__main__":
    main()