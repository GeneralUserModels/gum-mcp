import os

# from dotenv import load_dotenv
# load_dotenv()

from contextlib import asynccontextmanager
from dataclasses import dataclass
from collections.abc import AsyncIterator

from datetime import timedelta
from typing import Optional
from mcp.server.fastmcp import FastMCP, Context
from datetime import datetime, timezone
from gum import gum
from gum.db_utils import get_related_observations

@dataclass
class AppContext:
    gum_instance: gum

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    gum_instance = gum(os.environ["GUM_USER_NAME"])

    # NOTE: this doesn't listen to events- it just connects to the db
    # you'll need to start a seperate GUM listener to listen to Screen, for example-
    
    try:
        await gum_instance.connect_db()
    except Exception as e:
        print(e)
        raise e
    finally:
        yield AppContext(gum_instance=gum_instance)

mcp = FastMCP("gum", lifespan=app_lifespan)

@mcp.tool()
async def get_user_context(
    ctx: Context,
    query: str,
    start_hh_mm_ago: Optional[str] = None,
    end_hh_mm_ago: Optional[str] = None,
) -> str:
    """
    Retrieve context for a user query within a time window.

    Args:
        query: The user's query text (will be pre-processed by a lexical
            retrieval model such as BM25).
        start_hh_mm_ago: **Lower bound** of the window, expressed as a string
            in the form ``"HH:MM"`` meaning "HH hours and MM minutes ago from
            now".  For example, ``"01:00"`` = one hour ago.  Pass ``None`` if no
            lower bound is needed.
        end_hh_mm_ago: **Upper bound** of the window, also a ``"HH:MM"`` string
            relative to now (e.g., ``"00:10"`` = ten minutes ago).  Pass
            ``None`` for an open-ended upper bound.

    Returns:
        A string containing the retrieved contextual information.
    """

    # Convert time strings to datetime objects
    now = datetime.now(timezone.utc)
    start_time = None
    end_time = None

    if start_hh_mm_ago:
        hours, minutes = map(int, start_hh_mm_ago.split(':'))
        start_time = now - timedelta(hours=hours, minutes=minutes)

    if end_hh_mm_ago:
        hours, minutes = map(int, end_hh_mm_ago.split(':'))
        end_time = now - timedelta(hours=hours, minutes=minutes)

    # Query gum for relevant propositions
    gum_instance = ctx.request_context.lifespan_context.gum_instance

    results = await gum_instance.query(
        query,
        start_time=start_time,
        end_time=end_time
    )

    # Format results into a readable string
    if not results:
        return "No relevant context found for the given query and time window."

    context_parts = []
    async with gum_instance._session() as session:
        for proposition, score in results:
            # Format proposition details
            prop_text = f"• {proposition.text}"
            if proposition.reasoning:
                prop_text += f"\n  Reasoning: {proposition.reasoning}"
            if proposition.confidence:
                prop_text += f"\n  Confidence: {proposition.confidence}"
            prop_text += f"\n  Relevance Score: {score:.2f}"
            
            # Get and format related observations
            observations = await get_related_observations(session, proposition.id)
            if observations:
                prop_text += "\n  Supporting Observations:"
                for obs in observations:
                    prop_text += f"\n    - [{obs.observer_name}] {obs.content}"
            
            context_parts.append(prop_text)

    return "\n\n".join(context_parts)
