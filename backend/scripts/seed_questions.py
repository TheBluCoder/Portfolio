import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


DEFAULT_QUESTIONS = [
    "Who is Ikeoluwa?",
    "Tell me about Ikeoluwa Oladele.",
    "What is Ikeoluwa's background?",
    "What does Ikeoluwa study?",
    "What school does Ikeoluwa attend?",
    "What is Ikeoluwa's education?",
    "What are Ikeoluwa's technical skills?",
    "What programming languages does Ikeoluwa use?",
    "What frameworks has Ikeoluwa worked with?",
    "What backend technologies does Ikeoluwa know?",
    "What frontend technologies does Ikeoluwa know?",
    "What AI projects has Ikeoluwa built?",
    "What projects has Ikeoluwa worked on?",
    "What do we know about this project?",
    "Tell me about this project.",
    "What can you tell me about the selected project?",
    "How does this project work?",
    "What technologies were used in this project?",
    "What was Ikeoluwa's role in this project?",
    "Is this project live?",
    "Is this project testable?",
    "Is this project discontinued?",
    "Is there a live demo link for this project?",
    "Where is the link to this project?",
    "Tell me about Ikeoluwa's portfolio projects.",
    "Tell me about CiteMe.",
    "How does CiteMe work?",
    "What problem does CiteMe solve?",
    "Tell me about Git Mentor.",
    "What is GitRepoGuide?",
    "What was Ikeoluwa's role in Git Mentor?",
    "What has Ikeoluwa deployed?",
    "What cloud platforms has Ikeoluwa used?",
    "What is Ikeoluwa's experience with Azure?",
    "What is Ikeoluwa's experience with FastAPI?",
    "What is Ikeoluwa's experience with Vue?",
    "What is Ikeoluwa's experience with RAG?",
    "What is Ikeoluwa's experience with Pinecone?",
    "What is Ikeoluwa's experience with Gemini?",
    "What internships or work experience does Ikeoluwa have?",
    "What professional experience does Ikeoluwa have?",
    "What are Ikeoluwa's interests?",
    "What are Ikeoluwa's hobbies?",
    "How can I contact Ikeoluwa?",
    "Where can I find Ikeoluwa's GitHub?",
    "Where can I find Ikeoluwa's LinkedIn?",
    "Is Ikeoluwa available for work?",
    "What kind of roles is Ikeoluwa interested in?",
    "Why should someone hire Ikeoluwa?",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed the Pinecone questions index used by the portfolio topic gate."
    )
    parser.add_argument(
        "--index",
        default=os.getenv("TOPIC_GATE_INDEX", "questions"),
        help="Pinecone index name. Defaults to TOPIC_GATE_INDEX or 'questions'.",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Optional JSON file containing a list of question strings or objects with a text field.",
    )
    return parser.parse_args()


def load_questions(path: Path | None) -> list[str]:
    if path is None:
        return DEFAULT_QUESTIONS

    raw_data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw_data, list):
        raise ValueError("Question seed file must contain a JSON list.")

    questions: list[str] = []
    for item in raw_data:
        question = extract_question_text(item)
        if question:
            questions.append(question)
    return questions


def extract_question_text(item: Any) -> str:
    if isinstance(item, str):
        return item.strip()
    if isinstance(item, dict):
        value = item.get("text") or item.get("question")
        return value.strip() if isinstance(value, str) else ""
    return ""


def dedupe_questions(questions: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for question in questions:
        key = question.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(question)
    return deduped


async def seed_questions(index_name: str, questions: list[str]) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))

    from src.models.schemas import Content
    from src.services.pinecone_service import PineconeService

    pinecone_service = PineconeService()
    documents = [
        Content(id=f"question-{index + 1:03}", text=question)
        for index, question in enumerate(questions)
    ]

    try:
        await pinecone_service.upsert_documents(index_name, documents)
    finally:
        await pinecone_service.close()


async def main() -> None:
    load_dotenv()
    args = parse_args()
    questions = dedupe_questions(load_questions(args.file))
    if not questions:
        raise ValueError("No questions found to seed.")

    await seed_questions(
        index_name=args.index,
        questions=questions,
    )
    print(f"Seeded {len(questions)} questions into {args.index}.")


if __name__ == "__main__":
    asyncio.run(main())
