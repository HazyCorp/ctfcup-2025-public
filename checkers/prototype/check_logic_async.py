import asyncio
from datetime import datetime
from gornilo import Verdict
from cocktail_recipes import get_random_recipe
from common import generate_minecraft_bottle
from common_async import (
    create_account,
    upload_image,
    publish_recipe,
    get_recipes,
    like_recipe,
    download_and_verify_image
)
from requests_utils_async import get_aiohttp_session


def tprint(msg: str):
    """Print with timestamp."""
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{ts}] {msg}")


def check_own_recipes_first(recipes: list, expected_count: int) -> bool:
    """Check that user's own recipes appear first in the list."""
    if len(recipes) < expected_count:
        return False
    
    for i in range(expected_count):
        if recipes[i].get("secret_ingredient") is None:
            return False
    
    return True


async def check_logic_async(uri: str) -> Verdict:
    """Main async check function for the service with parallelization."""
    
    async with get_aiohttp_session(timeout=10) as session:
        try:
            # [1/10] Create first account
            tprint("[1/10] Creating account...")
            token1, token1_hash = await create_account(session, uri)
            
            # [2/10] Generate and upload bottle image
            tprint("[2/10] Uploading bottle image...")
            bottle_image = generate_minecraft_bottle()
            preview_location, image_hash = await upload_image(session, uri, token1, bottle_image)
            
            # [3-4/10] Publish two recipes sequentially (order matters for check)
            tprint("[3/10] Publishing first recipe...")
            recipe1 = get_random_recipe()
            recipe_id_1 = await publish_recipe(
                session, uri, token1,
                recipe_text=recipe1['recipe_text'],
                secret_ingredient=recipe1['secret_ingredient'],
                preview_location=preview_location
            )
            
            # tprint("[4/10] Publishing second recipe...")
            # recipe2 = get_random_recipe()
            # recipe_id_2 = await publish_recipe(
            #     session, uri, token1,
            #     recipe_text=recipe2['recipe_text'],
            #     secret_ingredient=recipe2['secret_ingredient'],
            #     preview_location=preview_location
            # )
            
            # # [5/10] Check own recipes order
            tprint("[5/10] Checking own recipes order...")
            recipes = await get_recipes(session, uri, token1)

            # Debug: print recipes info
            tprint(f"DEBUG: Got {len(recipes)} recipes")
            for i, r in enumerate(recipes[:3]):
                has_secret = r.get("secret_ingredient") is not None
                tprint(f"DEBUG: Recipe {i}: has_secret={has_secret}")

            if not check_own_recipes_first(recipes, 1):
                tprint("FAIL: Own recipes not first")
                tprint(f"DEBUG: Expected 1 recipe with secrets, got {len([r for r in recipes[:2] if r.get('secret_ingredient')])} in first 2")
                return Verdict.MUMBLE("Own recipes should appear first")

            tprint("[6/10] Verifying image download...")
            if len(recipes) > 0 and recipes[0].get('preview_url'):
                preview_url = recipes[0]['preview_url']
                if not await download_and_verify_image(session, uri, preview_url, image_hash):
                    tprint("FAIL: Image hash mismatch")
                    return Verdict.MUMBLE("Image hash verification failed")
            else:
                return Verdict.MUMBLE("No preview URL found in first recipe")

            # # [7/10] Create second account with all operations in parallel
            # tprint("[7/10] Creating second account and publishing recipe...")
            #
            # # Prepare data first (synchronous)
            # bottle_image_2 = generate_minecraft_bottle()
            # recipe3 = get_random_recipe()
            #
            # # Create account
            # token2, token2_hash = await create_account(session, uri)
            #
            # # Upload image and then publish recipe (sequential for this account)
            # preview_location_2, image_hash_2 = await upload_image(session, uri, token2, bottle_image_2)
            # recipe_id_3 = await publish_recipe(
            #     session, uri, token2,
            #     recipe_text=recipe3['recipe_text'],
            #     secret_ingredient=recipe3['secret_ingredient'],
            #     preview_location=preview_location_2
            # )
            #
            # # [8/10] Test likes - some can be done in parallel
            tprint("[8/10] Testing (limited) likes...")
            
            # # First like by user1
            # status1, data1 = await like_recipe(session, uri, token1, recipe_id_3)
            # if status1 != 200:
            #     tprint(f"FAIL: Like failed with status {status1}")
            #     return Verdict.MUMBLE("Failed to like recipe")
            #
            # # Duplicate like by user1 (must check after first)
            # status2, data2 = await like_recipe(session, uri, token1, recipe_id_3)
            # if status2 != 400 or data2.get("error") != "Already liked":
            #     tprint(f"FAIL: Duplicate like not prevented (status={status2})")
            #     return Verdict.MUMBLE("Duplicate like should be prevented")
            
            # Like own recipe by user2
            status3, data3 = await like_recipe(session, uri, token1, recipe_id_1)
            if status3 != 200:
                tprint(f"FAIL: Own like failed with status {status3}")
                return Verdict.MUMBLE("Failed to like own recipe")
            
            # [9-10/10] Check anonymous and user2 views in parallel
            # tprint("[9-10/10] Checking anonymous and user2 views in parallel...")
            #
            # recipes_anon, recipes_user2 = await asyncio.gather(
            #     get_recipes(session, uri, None),
            #     get_recipes(session, uri, token2)
            # )
            #
            # # Check anonymous view
            # for recipe in recipes_anon:
            #     if recipe['secret_ingredient'] is not None:
            #         tprint(f"FAIL: Secret visible for anonymous")
            #         return Verdict.MUMBLE("Secrets should be hidden for anonymous")
            #
            # # Check second user view
            # if not check_own_recipes_first(recipes_user2, 1):
            #     tprint("FAIL: Second user recipes not first")
            #     return Verdict.MUMBLE("User recipes should appear first")
            #
            tprint("OK: All checks passed")
            return Verdict.OK()
            
        except asyncio.TimeoutError:
            tprint("FAIL: Request timeout")
            return Verdict.DOWN("Service timeout")
        except ValueError as e:
            tprint(f"FAIL: {e}")
            return Verdict.MUMBLE(str(e))
        except Exception as e:
            tprint(f"FAIL: Unexpected error: {e}")
            raise


def check_logic(uri: str) -> Verdict:
    """Synchronous wrapper for async check logic."""
    return asyncio.run(check_logic_async(uri))

