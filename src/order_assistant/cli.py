"""Composition root and command-line entry point."""

import argparse
import logging

from order_assistant.service import answer_request

logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="LangChain / LangGraph order assistant")
    parser.add_argument("mode", choices=["graph", "agent", "hybrid", "rag", "index"])
    parser.add_argument("--order-id", default="", help="Numeric ID for graph/hybrid mode")
    parser.add_argument("--question", help="Natural-language request for agent/rag mode")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    if args.mode in {"agent", "rag"} and (not args.question or not args.question.strip()):
        parser.error(f"{args.mode} mode requires a nonempty --question")
    if args.question and len(args.question) > 2000:
        parser.error("question must be at most 2000 characters")
    try:
        if args.mode == "index":
            from dotenv import load_dotenv

            from order_assistant.vector_store import get_policy_index

            load_dotenv()
            index = get_policy_index()
            print(f"Indexed {index.sync()} policy passages in Chroma.")
            return 0
        request = args.question if args.mode in {"agent", "rag"} else args.order_id
        print(answer_request(args.mode, request))
        return 0
    except ImportError:
        logger.error('Dependencies missing. Run: python -m pip install -e ".[ui]"')
    except ValueError as exc:
        logger.error("%s", exc)
    except Exception as exc:
        logger.error(
            "Request failed (%s). Check provider access and connectivity.", type(exc).__name__
        )
    return 1
