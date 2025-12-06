from datetime import datetime
from gornilo import Verdict
from common_async import get_recipes
from requests_utils_async import get_aiohttp_session


def tprint(msg: str):
    """Print with timestamp."""
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{ts}] {msg}")


async def get_logic_async(uri: str, token: str, flag: str) -> Verdict:
    """Async version of get_logic."""
    async with get_aiohttp_session(timeout=10) as session:
        tprint("[GET] Fetching recipes...")
        recipes = await get_recipes(session, uri, token)

        for recipe in recipes:
            if recipe.get('secret_ingredient') == flag:
                tprint("OK: Flag found in recipe")
                return Verdict.OK()

        tprint(f"FAIL: Flag not found in {len(recipes)} recipes")
        return Verdict.CORRUPT("could not find placed secret ingredient")

