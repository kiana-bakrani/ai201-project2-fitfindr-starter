"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage:
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import re

from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.
    """
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
    }


# ── helper: parse query ───────────────────────────────────────────────────────

def _parse_query(query: str) -> dict:
    """
    Extract a simple description, size, and max_price from the user's query.

    This is intentionally rule-based instead of LLM-based so the behavior is
    easy to explain in planning.md and easy to test.
    """
    query_lower = query.lower()

    description = query_lower
    size = None
    max_price = None

    # Extract max price from phrases like "under $30" or "$30".
    price_match = re.search(r"\$?(\d+(?:\.\d+)?)", query_lower)
    if price_match:
        max_price = float(price_match.group(1))

    # Extract common clothing sizes if mentioned.
    size_patterns = [
        "xxs", "xs", "s/m", "m/l", "xl", "xxl",
        "small", "medium", "large",
        "size s", "size m", "size l",
        "w27", "w28", "w29", "w30", "w31", "w32",
        "us 7", "us 8", "us 8.5", "us 9",
    ]

    for pattern in size_patterns:
        if pattern in query_lower:
            if pattern == "small":
                size = "S"
            elif pattern == "medium":
                size = "M"
            elif pattern == "large":
                size = "L"
            elif pattern.startswith("size "):
                size = pattern.replace("size ", "").upper()
            else:
                size = pattern.upper()
            break

    # Remove price text so search focuses more on item/style words.
    description = re.sub(r"under\s+\$?\d+(?:\.\d+)?", "", description)
    description = re.sub(r"\$?\d+(?:\.\d+)?", "", description)

    # Remove size text if found.
    if size:
        description = description.replace(f"size {size.lower()}", "")
        description = description.replace(size.lower(), "")

    # Remove common filler phrases.
    filler_phrases = [
        "i'm looking for",
        "im looking for",
        "looking for",
        "i want",
        "find me",
        "what's out there",
        "whats out there",
        "and how would i style it",
        "how would i style it",
    ]

    for phrase in filler_phrases:
        description = description.replace(phrase, "")

    description = description.strip(" ,.?")

    if not description:
        description = query_lower

    return {
        "description": description,
        "size": size,
        "max_price": max_price,
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query: Natural language user request.
        wardrobe: User's wardrobe dict.

    Returns:
        The session dict after the interaction completes.
    """
    session = _new_session(query, wardrobe)

    # Step 1: Parse the user's query.
    parsed = _parse_query(query)
    session["parsed"] = parsed

    description = parsed["description"]
    size = parsed["size"]
    max_price = parsed["max_price"]

    # Step 2: Search listings first.
    results = search_listings(description, size=size, max_price=max_price)
    session["search_results"] = results

    # Step 3: If search fails, stop early.
    if not results:
        session["error"] = (
            "I couldn't find listings that match that description, size, and budget. "
            "Try a broader description, a different size, or a higher max price."
        )
        return session

    # Step 4: Store the top result in session state.
    session["selected_item"] = results[0]

    # Step 5: Suggest an outfit using the selected item and wardrobe.
    outfit = suggest_outfit(session["selected_item"], wardrobe)
    session["outfit_suggestion"] = outfit

    # Step 6: If outfit generation fails, stop early.
    if not outfit or not outfit.strip():
        session["error"] = (
            "I found a listing, but I couldn't generate an outfit suggestion for it."
        )
        return session

    # Step 7: Create the fit card using the outfit and selected item.
    fit_card = create_fit_card(session["outfit_suggestion"], session["selected_item"])
    session["fit_card"] = fit_card

    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )

    print(f"Parsed: {session['parsed']}")

    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )

    print(f"Parsed: {session2['parsed']}")
    print(f"Error message: {session2['error']}")
    print(f"Selected item: {session2['selected_item']}")
    print(f"Outfit suggestion: {session2['outfit_suggestion']}")
    print(f"Fit card: {session2['fit_card']}")