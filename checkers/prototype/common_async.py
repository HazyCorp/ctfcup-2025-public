import aiohttp
from io import BytesIO
from typing import Optional, Tuple, Dict
import hashlib
from common import generate_minecraft_bottle
from requests_utils_async import retry_request


async def create_account(session: aiohttp.ClientSession, base_uri: str) -> Tuple[str, str]:
    """Create a new account and return token with hash."""
    async def do_request():
        async with session.get(f"{base_uri}/obtain_account") as response:
            if response.status != 200:
                raise ValueError(f"Failed to create account: {response.status}")
            token = (await response.text()).strip()
            return token
    
    token = await retry_request(do_request)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token, token_hash


async def upload_image(session: aiohttp.ClientSession, base_uri: str, 
                       token: str, image_data: BytesIO) -> Tuple[str, str]:
    """Upload image to the service and return location with hash."""
    headers = {"X-Token": token}
    
    image_bytes = image_data.getvalue()
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    image_data.seek(0)
    
    async def do_request():
        data = aiohttp.FormData()
        image_data.seek(0)  # Reset on retry
        data.add_field('file', image_data, filename='preview.png', content_type='image/png')
        
        async with session.post(f"{base_uri}/upload", headers=headers, data=data) as response:
            if response.status != 200:
                raise ValueError(f"Failed to upload image: {response.status}")
            upload_data = await response.json()
            return upload_data.get("loc")
    
    preview_location = await retry_request(do_request)
    return preview_location, image_hash


async def publish_recipe(session: aiohttp.ClientSession, base_uri: str, token: str, 
                          recipe_text: str, secret_ingredient: str, 
                          preview_location: str) -> str:
    """Publish a recipe to the service."""
    headers = {"X-Token": token, "Content-Type": "application/json"}
    
    recipe_data = {
        "recipe_text": recipe_text,
        "secret_ingredient": secret_ingredient,
        "preview_location": preview_location
    }
    
    async def do_request():
        async with session.post(f"{base_uri}/publish_recipe", headers=headers, 
                                json=recipe_data) as response:
            if response.status != 200:
                raise ValueError(f"Failed to publish recipe: {response.status}")
            publish_data = await response.json()
            return publish_data.get("recipe_id")
    
    return await retry_request(do_request)


async def get_recipes(session: aiohttp.ClientSession, base_uri: str, 
                      token: Optional[str] = None) -> list:
    """Get recipes list from service."""
    headers = {"X-Token": token} if token else {}
    
    async def do_request():
        async with session.get(f"{base_uri}/recipes", headers=headers) as response:
            if response.status != 200:
                raise ValueError(f"Failed to get recipes: {response.status}")
            recipes_data = await response.json()
            return recipes_data.get("recipes", [])
    
    return await retry_request(do_request)


async def like_recipe(session: aiohttp.ClientSession, base_uri: str, 
                      token: str, recipe_id: str) -> Tuple[int, Dict]:
    """Like a recipe."""
    headers = {"X-Token": token, "Content-Type": "application/json"}
    
    async def do_request():
        async with session.put(f"{base_uri}/like_recipe", headers=headers,
                                json={"recipe_id": recipe_id}) as response:
            return response.status, await response.json()
    
    return await retry_request(do_request)


async def download_and_verify_image(session: aiohttp.ClientSession, base_uri: str, 
                                     preview_url: str, expected_hash: str) -> bool:
    """Download image from preview URL and verify hash."""
    full_url = base_uri.strip("/") + "/" + preview_url.strip("/")
    
    async def do_request():
        async with session.get(full_url) as response:
            if response.status != 200:
                print(f"Failed to download image: {response.status}")
                return None
            return await response.read()
    
    content = await retry_request(do_request)
    if content is None:
        return False
    
    downloaded_hash = hashlib.sha256(content).hexdigest()
    return downloaded_hash == expected_hash
