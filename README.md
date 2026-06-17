# FitFindr

FitFindr is a multi-tool AI agent that helps users search for secondhand clothing, style a selected item with an existing wardrobe, and generate a short shareable outfit caption. The project demonstrates tool design, a planning loop, session state, and error handling across a multi-step workflow.

## How to Run

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```bash
GROQ_API_KEY=your_key_here
```

Run the app:

```bash
python app.py
```

Open the local URL printed in the terminal.

Run tests:

```bash
PYTHONPATH=. pytest tests/
```

## Tool Inventory

### `search_listings(description, size, max_price)`

**Inputs:**

* `description` (`str`): Natural language description of the item the user wants, such as `"vintage graphic tee"`.
* `size` (`str | None`): Optional size filter, such as `"M"`, `"S/M"`, `"W30"`, or `"US 8"`.
* `max_price` (`float | None`): Optional maximum price.

**Output:**

* Returns a `list[dict]` of matching listing dictionaries sorted by relevance.
* Each listing includes `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.
* Returns `[]` if no listings match.

**Purpose:**
This tool searches the mock secondhand listings dataset and finds items that match the user’s description, size, and budget.

### `suggest_outfit(new_item, wardrobe)`

**Inputs:**

* `new_item` (`dict`): The selected listing returned by `search_listings`.
* `wardrobe` (`dict`): A wardrobe object with an `items` key containing wardrobe item dictionaries.

**Output:**

* Returns a `str` containing one or more outfit suggestions.
* If the wardrobe is empty, it returns general styling advice instead of crashing.

**Purpose:**
This tool uses the selected thrifted item and the user’s wardrobe to suggest a complete outfit.

### `create_fit_card(outfit, new_item)`

**Inputs:**

* `outfit` (`str`): The outfit suggestion returned by `suggest_outfit`.
* `new_item` (`dict`): The selected listing returned by `search_listings`.

**Output:**

* Returns a short caption-style `str` that could be used as an outfit post or fit card.
* If the outfit input is empty, it returns a clear message saying an outfit suggestion is needed first.

**Purpose:**
This tool turns the selected thrift item and outfit suggestion into a short shareable caption.

## Planning Loop

The agent starts by creating a new `session` dictionary for the interaction. It then parses the user query with simple rule-based parsing to extract:

* `description`
* `size`
* `max_price`

The agent always calls `search_listings` first because the rest of the workflow depends on finding a real listing.

After search:

1. If `search_listings` returns an empty list, the agent stores a helpful message in `session["error"]` and returns early.
2. If results exist, the agent stores the full list in `session["search_results"]`.
3. The top result is stored in `session["selected_item"]`.
4. The agent calls `suggest_outfit(session["selected_item"], wardrobe)`.
5. The outfit suggestion is stored in `session["outfit_suggestion"]`.
6. If the outfit suggestion is empty, the agent stores an error and stops early.
7. Otherwise, the agent calls `create_fit_card(session["outfit_suggestion"], session["selected_item"])`.
8. The fit card is stored in `session["fit_card"]`.

The planning loop is not a fixed sequence that ignores results. It branches after search and stops early if there are no listings, so the later tools do not receive missing or invalid input.

## State Management

FitFindr uses a `session` dictionary as the shared state for one complete interaction.

The session tracks:

* `query`: the original user query
* `parsed`: extracted search parameters
* `search_results`: all matching listings
* `selected_item`: the top listing selected for styling
* `wardrobe`: the wardrobe used for outfit generation
* `outfit_suggestion`: output from `suggest_outfit`
* `fit_card`: output from `create_fit_card`
* `error`: message explaining why the workflow stopped early, if applicable

State passes data between tools. For example, `search_listings` returns a selected item, the agent stores it in `session["selected_item"]`, then passes that same item into `suggest_outfit` and `create_fit_card`.

## Error Handling Strategy

| Tool              | Failure mode                     | Agent response                                                                                                         |
| ----------------- | -------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `search_listings` | No listings match the query      | Returns `[]`. The agent stores an error message and stops early without calling `suggest_outfit` or `create_fit_card`. |
| `suggest_outfit`  | Wardrobe is empty                | Returns a general outfit suggestion using common basics instead of crashing.                                           |
| `suggest_outfit`  | Groq call fails                  | Returns a fallback styling suggestion string so the agent can continue.                                                |
| `create_fit_card` | Outfit input is missing or empty | Returns `"I need an outfit suggestion before I can create a fit card."` instead of raising an exception.               |
| `create_fit_card` | Groq call fails                  | Returns a fallback fit card using the selected item and outfit suggestion.                                             |

### Concrete Error Example

When the user enters:

```text
designer ballgown size XXS under $5
```

`search_listings` returns `[]`. The agent returns:

```text
I couldn't find listings that match that description, size, and budget. Try a broader description, a different size, or a higher max price.
```

The outfit and fit card panels remain blank because the agent stops early.

## Testing

The project includes pytest tests in `tests/test_tools.py`.

The tests cover:

* successful listing search
* empty listing search
* price filtering
* outfit suggestion with an empty wardrobe
* outfit suggestion with the example wardrobe
* fit card failure when outfit input is empty
* successful fit card generation

Final test result:

```bash
7 passed
```

## Example Interaction

User query:

```text
vintage graphic tee under $30
```

The agent parses:

```python
{
    "description": "a vintage graphic tee",
    "size": None,
    "max_price": 30.0
}
```

The agent calls `search_listings` and selects the top matching item, such as `Y2K Baby Tee — Butterfly Print`.

Then it calls `suggest_outfit` using the selected item and the chosen wardrobe. Finally, it calls `create_fit_card` using the outfit suggestion and selected item.

The app displays:

1. The selected listing
2. The outfit idea
3. The final fit card caption

## Spec Reflection

One way the spec helped was that it forced me to define the tool interfaces and failure behavior before coding. That made the implementation easier because each function had a clear input, output, and responsibility.

One way the implementation diverged from the initial plan was query parsing. The original planning loop described extracting `description`, `size`, and `max_price`, but did not require a specific parsing method. I used rule-based parsing instead of an LLM because it was easier to test, easier to explain, and reliable enough for the project examples.

## AI Usage

### Instance 1: Tool implementation

I used ChatGPT to help implement the three required tools from the tool specs in `planning.md`. I provided the Tool 1, Tool 2, and Tool 3 sections, including the expected inputs, outputs, and failure modes. I reviewed the generated code to make sure `search_listings` used `load_listings()`, `suggest_outfit` handled an empty wardrobe, and `create_fit_card` returned a message instead of crashing when the outfit input was empty.

### Instance 2: Planning loop and state

I used ChatGPT to help implement `run_agent()` in `agent.py`. I provided the Planning Loop, State Management, and Architecture sections from `planning.md`. I checked that the generated code searched first, stopped early when no results were found, stored the selected item in `session["selected_item"]`, and passed state into the next tools instead of asking the user to re-enter information.

### Instance 3: Debugging and testing

I used ChatGPT to help debug the Groq API call when the tool returned a fallback response. The issue was an invalid API key in `.env`. After fixing the key, I reran the tool tests and confirmed that the LLM-generated outfit suggestions worked.
