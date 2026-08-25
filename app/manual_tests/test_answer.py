from src.llm.answer import answer_question

def main():
    question = "How do geopolitical tensions affect gold?"
    # question = "who win yesterday barca or real"

    print("=" * 80)
    print("QUESTION:")
    print(question)
    print("=" * 80)
    result = answer_question(question)
    print(result["answer"])
    


if __name__ == "__main__":
    main()