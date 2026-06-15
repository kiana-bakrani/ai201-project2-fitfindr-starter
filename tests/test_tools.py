from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_empty_wardrobe, get_example_wardrobe


def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)

    assert isinstance(results, list)
    assert len(results) > 0
    assert isinstance(results[0], dict)


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)

    assert results == []


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=50)

    assert all(item["price"] <= 50 for item in results)


def test_suggest_outfit_empty_wardrobe():
    item = search_listings("vintage graphic tee", size=None, max_price=30)[0]
    outfit = suggest_outfit(item, get_empty_wardrobe())

    assert isinstance(outfit, str)
    assert len(outfit.strip()) > 0


def test_suggest_outfit_example_wardrobe():
    item = search_listings("vintage graphic tee", size=None, max_price=30)[0]
    outfit = suggest_outfit(item, get_example_wardrobe())

    assert isinstance(outfit, str)
    assert len(outfit.strip()) > 0


def test_create_fit_card_empty_outfit():
    item = search_listings("vintage graphic tee", size=None, max_price=30)[0]
    fit_card = create_fit_card("", item)

    assert isinstance(fit_card, str)
    assert "outfit suggestion" in fit_card.lower()


def test_create_fit_card_returns_caption():
    item = search_listings("vintage graphic tee", size=None, max_price=30)[0]
    outfit = "Pair it with baggy jeans and chunky sneakers for a casual Y2K streetwear look."
    fit_card = create_fit_card(outfit, item)

    assert isinstance(fit_card, str)
    assert len(fit_card.strip()) > 0