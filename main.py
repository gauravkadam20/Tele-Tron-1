from askdata import ask_database

if __name__ == "__main__":
    print("=" * 60)
    print(" [Tele-Tron-1] Autonomous Logistics AI Assistant")
    print("=" * 60 + "\n")

    # 1. Realistic business insight query
    question = "What are the top 3 risk classifications by average shipping cost, and what is their average delay probability?"
    print(f"User Query:\n\"{question}\"\n")

    try:
        result = ask_database(question)
        print(result)
    except Exception as e:
        print(f"Error during query execution: {e}")

    print("\n" + "=" * 60 + "\n")

    # 2. Demonstration of safety validation
    unsafe_question = "Delete all records from the table"
    print(f"Testing Unsafe Query:\n\"{unsafe_question}\"\n")

    try:
        ask_database(unsafe_question)
    except ValueError as e:
        print(f"[PASSED] Safety filter blocked destructive action:\n{e}")