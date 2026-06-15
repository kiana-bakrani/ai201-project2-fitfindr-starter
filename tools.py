"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.
    """
    listings = load_listings()

    query_words = set(description.lower().split())
    matches = []

    for item in listings:
        # Filter by max price if provided
        if max_price is not None and item["price"] > max_price:
            continue

        # Filter by size if provided
        if size is not None:
            requested_size = size.lower()
            item_size = item["size"].lower()
            if requested_size not in item_size:
                continue

        # Combine searchable fields into one lowercase string
        searchable_text = " ".join([
            item.get("title") or "",
            item.get("description") or "",
            item.get("category") or "",
            " ".join(item.get("style_tags") or []),
            " ".join(item.get("colors") or []),
            item.get("brand") or "",
            item.get("platform") or "",
        ]).lower()

        # Score by keyword overlap
        score = sum(1 for word in query_words if word in searchable_text)

        if score > 0:
            matches.append((score, item))

    # Sort best matches first
    matches.sort(key=lambda pair: pair[0], reverse=True)

    return [item for score, item in matches]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.
    """
    client = _get_groq_client()

    wardrobe_items = wardrobe.get("items", [])

    item_summary = f"""
Title: {new_item.get("title")}
Description: {new_item.get("description")}
Category: {new_item.get("category")}
Style tags: {", ".join(new_item.get("style_tags") or [])}
Colors: {", ".join(new_item.get("colors") or [])}
Condition: {new_item.get("condition")}
Price: ${new_item.get("price")}
Platform: {new_item.get("platform")}
"""

    if not wardrobe_items:
        prompt = f"""
You are FitFindr, a secondhand fashion styling assistant.

The user is considering this thrifted item:
{item_summary}

The user's wardrobe is empty or unavailable.

Suggest 1 complete outfit using common wardrobe basics someone might already own.
Be specific, practical, and stylish. Mention the overall vibe.
Keep the response to 3-5 sentences.
"""
    else:
        wardrobe_summary = "\n".join(
            f"- {item.get('name')} "
            f"({item.get('category')}, "
            f"colors: {', '.join(item.get('colors') or [])}, "
            f"style: {', '.join(item.get('style_tags') or [])})"
            for item in wardrobe_items
        )

        prompt = f"""
You are FitFindr, a secondhand fashion styling assistant.

The user is considering this thrifted item:
{item_summary}

The user's current wardrobe:
{wardrobe_summary}

Suggest 1-2 complete outfit combinations using the thrifted item and specific named pieces from the wardrobe.
Explain briefly why the pieces work together.
Keep the response practical, stylish, and concise.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a concise fashion styling assistant for secondhand clothing.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Groq error in suggest_outfit: {e}")
        return (
            f"Style {new_item.get('title', 'this thrifted item')} with simple basics "
            "like well-fitting jeans, clean sneakers or boots, and one layering piece. "
            "Keep the colors balanced and let the thrifted item be the main focus."
        )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.
    """
    if not outfit or not outfit.strip():
        return "I need an outfit suggestion before I can create a fit card."

    client = _get_groq_client()

    item_title = new_item.get("title", "this thrifted item")
    item_price = new_item.get("price", "unknown price")
    item_platform = new_item.get("platform", "a secondhand platform")
    item_colors = ", ".join(new_item.get("colors") or [])
    item_tags = ", ".join(new_item.get("style_tags") or [])

    prompt = f"""
You are FitFindr, a secondhand fashion assistant.

Create a short shareable outfit caption for this thrifted find.

Thrifted item:
- Title: {item_title}
- Price: ${item_price}
- Platform: {item_platform}
- Colors: {item_colors}
- Style tags: {item_tags}

Outfit suggestion:
{outfit}

Write a 2-4 sentence caption that sounds casual and authentic, like an Instagram or TikTok outfit post.
Mention the item name, price, and platform naturally once each.
Do not sound like a product description.
Make it specific to the outfit vibe.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You write casual, stylish, secondhand outfit captions.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.9,
            max_tokens=180,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Groq error in create_fit_card: {e}")
        return (
            f"Thrifted {item_title} for ${item_price} on {item_platform}. "
            f"Styled it around this vibe: {outfit}"
        )