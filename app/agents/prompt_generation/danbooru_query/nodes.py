"""Business nodes for the prompt_danbooru_query agent."""

import json
import re
import asyncio
from typing import Any, Dict, Iterable, List

import httpx
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.agents.prompt_generation.danbooru_query.state import PromptDanbooruQueryState
from app.services.ai_provider import AIProvider, ai_provider

DANBOORU_TAGS_URL = "https://danbooru.donmai.us/tags.json"


def normalize_tag_candidate(value: str) -> str:
    """Normalize one search candidate for Danbooru tag lookup."""

    return re.sub(r"\s+", "_", value.strip().lower())


def unique_nonempty(values: Iterable[str], limit: int = 12) -> List[str]:
    """Return de-duplicated non-empty strings while preserving order."""

    seen = set()
    result = []
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        result.append(text)
        seen.add(key)
        if len(result) >= limit:
            break
    return result


def collect_seed_terms(requirements: Dict[str, Any], user_input: str) -> List[str]:
    """Collect terms that do not require translation or tag knowledge."""

    seeds = []
    raw_request = str(requirements.get("raw_request") or user_input or "")
    subject = str(requirements.get("subject") or "")
    for value in [raw_request, subject]:
        if value and value.isascii():
            seeds.append(value)

    for token in re.findall(r"[A-Za-z][A-Za-z0-9_()'-]{1,}", raw_request):
        seeds.append(token)
    return unique_nonempty(seeds)


def parse_json_list(text: str) -> List[str]:
    """Parse a model response that should contain a JSON string list."""

    text = text.strip()
    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        text = match.group(0)
    data = json.loads(text)
    if not isinstance(data, list):
        return []
    return [str(item) for item in data]


async def generate_danbooru_search_terms(
    raw_request: str,
    state: PromptDanbooruQueryState,
) -> List[str]:
    """Ask the configured model for Danbooru search candidates."""

    if not raw_request.strip():
        return []

    model = ai_provider.get_model(
        model_name=state.get("model") or AIProvider.DEFAULT_MODEL,
        temperature=0,
    )
    response = await model.ainvoke(
        [
            SystemMessage(
                content=(
                    "You convert an image prompt request into Danbooru tag search "
                    "candidates. Return only a JSON array of short English or romanized "
                    "search terms. Do not invent final tags; these terms will be checked "
                    "against Danbooru."
                )
            ),
            HumanMessage(content=raw_request),
        ]
    )
    try:
        return unique_nonempty(parse_json_list(str(response.content)))
    except Exception:
        return []


async def query_one_danbooru_term(
    client: httpx.AsyncClient,
    raw_term: str,
) -> List[Dict[str, Any]]:
    """Query Danbooru for one normalized prefix term."""

    term = normalize_tag_candidate(raw_term)
    if not term:
        return []
    headers = {"User-Agent": "AgentWorkflowKit/0.1"}
    exact_response = await client.get(
        DANBOORU_TAGS_URL,
        params={
            "search[name_matches]": term,
            "search[hide_empty]": "yes",
            "limit": "8",
        },
        headers=headers,
    )
    exact_response.raise_for_status()
    exact_tags = exact_response.json()
    if isinstance(exact_tags, list) and exact_tags:
        return exact_tags

    prefix_response = await client.get(
        DANBOORU_TAGS_URL,
        params={
            "search[name_matches]": f"{term}*",
            "search[hide_empty]": "yes",
            "limit": "8",
        },
        headers=headers,
    )
    prefix_response.raise_for_status()
    prefix_tags = prefix_response.json()
    if not isinstance(prefix_tags, list):
        return []
    filtered = [
        item
        for item in prefix_tags
        if str(item.get("name") or "").startswith(f"{term}_")
    ]
    filtered = sorted(
        filtered,
        key=lambda item: int(item.get("post_count") or 0),
        reverse=True,
    )
    return filtered[:1]


def clean_danbooru_record(item: Dict[str, Any]) -> Dict[str, Any]:
    """Keep only Danbooru-provided tag fields used downstream."""

    return {
        "name": str(item.get("name") or ""),
        "category": int(item.get("category") or 0),
        "post_count": int(item.get("post_count") or 0),
    }


async def query_danbooru_tag_records(
    terms: Iterable[str],
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Query Danbooru and return existing tag records sorted by post count."""

    search_terms = unique_nonempty(terms, limit=8)
    async with httpx.AsyncClient(timeout=5.0) as client:
        results = await asyncio.gather(
            *(query_one_danbooru_term(client, term) for term in search_terms),
            return_exceptions=True,
        )

    tag_items: list[Dict[str, Any]] = []
    for result in results:
        if isinstance(result, Exception):
            continue
        tag_items.extend(result)

    tag_items = sorted(
        tag_items,
        key=lambda item: int(item.get("post_count") or 0),
        reverse=True,
    )
    found: list[Dict[str, Any]] = []
    seen = set()
    for item in tag_items:
        name = str(item.get("name") or "")
        if not name or name in seen:
            continue
        found.append(clean_danbooru_record(item))
        seen.add(name)
        if len(found) >= limit:
            break
    return found


async def query_tags_node(
    state: PromptDanbooruQueryState,
    config: RunnableConfig | None = None,
) -> Dict[str, Any]:
    """Query Danbooru for tags instead of using a local character map."""

    requirements = state.get("requirements_json") or {}
    raw_request = str(requirements.get("raw_request") or state.get("user_input") or "")
    seed_terms = collect_seed_terms(requirements, raw_request)
    model_terms = await generate_danbooru_search_terms(raw_request, state)
    search_terms = unique_nonempty([*seed_terms, *model_terms])

    tag_records: list[Dict[str, Any]] = []
    error = None
    try:
        tag_records = await query_danbooru_tag_records(search_terms)
    except Exception as exc:
        error = str(exc)

    tags = [record["name"] for record in tag_records]

    notes = {
        "source": "danbooru_api",
        "search_terms": search_terms,
        "miss": not tags,
    }
    if error:
        notes["error"] = error

    return {
        "danbooru_tags": tags,
        "danbooru_tag_records": tag_records,
        "tag_notes": json.dumps(notes, ensure_ascii=False),
        "messages": [
            AIMessage(
                content=(
                    f"Danbooru query returned {len(tags)} tags."
                    if tags
                    else "Danbooru query returned no tags."
                ),
                name="prompt_danbooru_query",
            )
        ],
    }
