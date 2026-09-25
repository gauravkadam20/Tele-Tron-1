import sys
from askdata import ask_database

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)
    print("=" * 60)
    print(" [Tele-Tron-1] Autonomous Logistics AI Assistant (P1 Operational)")
    print("=" * 60 + "\n")

    # 1. First business query
    q1 = "What are the top 3 risk classifications by average shipping cost, and what is their average delay probability?"
    print(f"Turn 1 Query:\n\"{q1}\"\n")

    try:
        res1 = ask_database(q1)
        print(res1)
    except Exception as e:
        print(f"Error during query execution: {e}")

    print("\n" + "-" * 60 + "\n")

    # 2. Multi-Turn Follow-Up Query
    q2 = "What are the historical demand levels for those specific risk tiers?"
    print(f"Turn 2 Follow-Up Query (Contextual Memory):\n\"{q2}\"\n")

    history = [
        {
            "question": q1,
            "sql": res1.sql,
            "assumptions": res1.assumptions,
            "summary": res1.summary,
        }
    ]

    try:
        res2 = ask_database(q2, chat_history=history)
        print(res2)
    except Exception as e:
        print(f"Error during follow-up query execution: {e}")

    print("\n" + "-" * 60 + "\n")

    # 3. In-Memory Cache Demonstration ($0 cost, 0 latency)
    print("Testing In-Memory Query Cache (Repeating Turn 1):\n")
    cached_res = ask_database(q1)
    print(cached_res)
    print(f"Is from cache: {cached_res.from_cache}")

    print("\n" + "=" * 60 + "\n")

    # 4. Demonstration of safety validation
    unsafe_question = "Delete all records from the table"
    print(f"Testing Unsafe Query:\n\"{unsafe_question}\"\n")

    try:
        ask_database(unsafe_question)
    except ValueError as e:
        print(f"[PASSED] Safety filter blocked destructive action:\n{e}")