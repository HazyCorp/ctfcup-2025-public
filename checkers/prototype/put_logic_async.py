import base64
import json
from datetime import datetime
from gornilo import Verdict
from cocktail_recipes import get_random_recipe
from common import generate_minecraft_bottle
from common_async import create_account, upload_image, publish_recipe
from requests_utils_async import get_aiohttp_session


def tprint(msg: str):
    """Print with timestamp."""
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{ts}] {msg}")


async def put_logic_async(uri: str, flag: str) -> Verdict:
    """Async version of put_logic."""
    async with get_aiohttp_session(timeout=10) as session:
        tprint("[PUT] Creating account...")
        token1, token1_hash = await create_account(session, uri)

        tprint("[PUT] Uploading bottle...")
        bottle_image = generate_minecraft_bottle()
        preview_location, image_hash = await upload_image(session, uri, token1, bottle_image)

        tprint("[PUT] Publishing recipe with flag...")
        recipe = get_random_recipe()

        await publish_recipe(
            session, uri, token1,
            recipe_text=recipe['recipe_text'],
            secret_ingredient=flag,
            preview_location=preview_location
        )
        tprint("[PUT] Recipe published")

        # Decode token to get access_key
        padding = len(token1) % 4
        if padding:
            token1 += '=' * (4 - padding)

        token = json.loads(base64.urlsafe_b64decode(token1).decode("utf-8"))
        access_key, secret_key = token[0].split(":")

        tprint("OK: Flag placed.")
        return Verdict.OK_WITH_FLAG_ID(access_key, token1)

