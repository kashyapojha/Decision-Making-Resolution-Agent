from __future__ import annotations

import argparse
import json

from .agent import ResolutionAgent
from .providers import DeterministicFallbackProvider, OpenAICompatibleProvider


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the decision-making resolution agent")
    parser.add_argument("request", nargs="+", help="Customer order issue")
    parser.add_argument("--provider", choices=["demo", "openai"], default="demo")
    parser.add_argument("--max-iterations", type=int, default=5)
    args = parser.parse_args()

    if args.provider == "openai":
        provider = OpenAICompatibleProvider()
    else:
        provider = DeterministicFallbackProvider()

    result = ResolutionAgent(
        provider=provider,
        max_iterations=args.max_iterations,
    ).run(" ".join(args.request))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
