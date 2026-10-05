"""
Runs eval/test_questions.csv against a live backend (start it first with
`uvicorn backend.app:app --reload`) and reports:
  - whether an answer was returned at all
  - whether the expected keyword/number shows up in the answer
  - whether RAG questions came back with a source citation

This is a simple keyword-containment eval, not exact-match grading —
good enough to demonstrate the idea of measuring correctness rather than
just eyeballing answers. Swap in stricter scoring as the project matures.
"""
import csv
import os
import sys

import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
TEST_FILE = os.path.join(os.path.dirname(__file__), "test_questions.csv")


def main():
    with open(TEST_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    passed, total = 0, len(rows)
    print(f"Running {total} eval questions against {BACKEND_URL} ...\n")

    for row in rows:
        question = row["question"]
        expected_contains = row["expected_answer_contains"].strip()

        try:
            r = requests.post(f"{BACKEND_URL}/ask", json={"question": question}, timeout=60)
            r.raise_for_status()
            result = r.json()
        except Exception as e:
            print(f"✗ ERROR  | {question}\n         {e}\n")
            continue

        answer = result.get("answer", "")
        has_citation = bool(result.get("sources"))
        ok = (not expected_contains) or (expected_contains.lower() in answer.lower())

        status = "✓ PASS" if ok else "✗ FAIL"
        if ok:
            passed += 1

        print(f"{status} | {question}")
        print(f"        answer: {answer[:160]}{'...' if len(answer) > 160 else ''}")
        if row["expected_tool"] == "rag":
            print(f"        citation returned: {has_citation}")
        print()

    print(f"Result: {passed}/{total} passed ({passed/total*100:.0f}%)")


if __name__ == "__main__":
    main()
