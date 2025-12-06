import os
import json
import threading
import time
from typing import List, Dict, Optional
from datetime import datetime
from datetime import UTC
import uuid

RECIPES_DIR = "recipes_data"
USER_INDEXES_DIR = os.path.join(RECIPES_DIR, "user_indexes")

# Background cache for latest recipe IDs (not full data - to keep likes fresh)
_recipes_id_cache: List[str] = []
_cache_lock = threading.Lock()
_cache_thread: Optional[threading.Thread] = None
_cache_running = False

CACHE_REFRESH_INTERVAL = 60  # seconds
CACHE_SIZE = 50


def _ensure_recipes_dir():
    os.makedirs(RECIPES_DIR, exist_ok=True)
    os.makedirs(USER_INDEXES_DIR, exist_ok=True)


def _refresh_recipes_cache():
    """Background task to refresh recipes ID cache with latest created recipes."""
    global _recipes_id_cache
    
    _ensure_recipes_dir()
    
    try:
        # Get files with mtime, sorted by newest first
        files_with_mtime = []
        for f in os.listdir(RECIPES_DIR):
            if f.endswith(".json"):
                filepath = os.path.join(RECIPES_DIR, f)
                try:
                    mtime = os.path.getmtime(filepath)
                    files_with_mtime.append((f, mtime))
                except OSError:
                    continue
        
        # Sort by mtime descending (newest first)
        files_with_mtime.sort(key=lambda x: x[1], reverse=True)
        
        # Take latest CACHE_SIZE file IDs only
        new_cache = [f[:-5] for f, _ in files_with_mtime[:CACHE_SIZE]]
        
        with _cache_lock:
            _recipes_id_cache = new_cache
            
    except Exception as e:
        print(f"[CACHE] Error refreshing cache: {e}")


def _cache_refresh_loop():
    """Background thread loop."""
    global _cache_running
    
    while _cache_running:
        _refresh_recipes_cache()
        time.sleep(CACHE_REFRESH_INTERVAL)


def start_cache_refresh():
    """Start background cache refresh thread."""
    global _cache_thread, _cache_running
    
    if _cache_thread is not None and _cache_thread.is_alive():
        return
    
    _cache_running = True
    _refresh_recipes_cache()  # Initial refresh
    
    _cache_thread = threading.Thread(target=_cache_refresh_loop, daemon=True)
    _cache_thread.start()


def stop_cache_refresh():
    """Stop background cache refresh thread."""
    global _cache_running
    _cache_running = False


def _get_cached_recipe_ids() -> List[str]:
    """Get recipe IDs from cache."""
    with _cache_lock:
        return _recipes_id_cache.copy()


def _get_user_index_path(user: str) -> str:
    safe_user = user.replace("/", "_").replace("\\", "_")
    return os.path.join(USER_INDEXES_DIR, f"{safe_user}.json")


def _load_user_index(user: str) -> List[str]:
    user_index_path = _get_user_index_path(user)
    if not os.path.exists(user_index_path):
        return []
    try:
        with open(user_index_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_user_index(user: str, recipe_ids: List[str]):
    user_index_path = _get_user_index_path(user)
    with open(user_index_path, "w") as f:
        json.dump(recipe_ids, f, indent=2)


def _add_recipe_to_user_index(user: str, recipe_id: str):
    recipe_ids = _load_user_index(user)
    if recipe_id not in recipe_ids:
        recipe_ids.append(recipe_id)
    _save_user_index(user, recipe_ids)


def publish_recipe(user: str, recipe_text: str, secret_ingredient: str, preview_location: str) -> str:
    _ensure_recipes_dir()
    
    recipe_id = str(uuid.uuid4())
    recipe_data = {
        "id": recipe_id,
        "user": user,
        "recipe_text": recipe_text,
        "secret_ingredient": secret_ingredient,
        "preview_location": preview_location,
        "created_at": datetime.now(UTC).isoformat(),
        "likes": 0,
        "liked_by": []
    }
    
    recipe_path = os.path.join(RECIPES_DIR, f"{recipe_id}.json")
    with open(recipe_path, "w") as f:
        json.dump(recipe_data, f, indent=2)
    
    _add_recipe_to_user_index(user, recipe_id)
    
    return recipe_id


def _load_recipe_raw(recipe_id: str) -> Optional[Dict]:
    recipe_path = os.path.join(RECIPES_DIR, f"{recipe_id}.json")
    if not os.path.exists(recipe_path):
        return None
    try:
        with open(recipe_path, "r") as f:
            recipe = json.load(f)
        if "likes" not in recipe:
            recipe["likes"] = 0
        if "liked_by" not in recipe:
            recipe["liked_by"] = []
        return recipe
    except (json.JSONDecodeError, KeyError):
        return None


def _apply_recipe_filters(recipe: Dict, current_user: Optional[str]) -> Dict:
    filtered = recipe.copy()
    filtered["user_liked"] = current_user in recipe.get("liked_by", []) if current_user else False
    if current_user != recipe["user"]:
        filtered["secret_ingredient"] = None
    filtered.pop("liked_by", None)
    return filtered


def get_recipes(current_user: Optional[str] = None) -> List[Dict]:
    _ensure_recipes_dir()
    
    # Get latest recipe IDs from cache (no listdir!)
    latest_recipe_ids = _get_cached_recipe_ids()
    
    if current_user:
        user_recipe_ids = _load_user_index(current_user)
        user_recipes = []
        
        for recipe_id in user_recipe_ids:
            recipe = _load_recipe_raw(recipe_id)
            if recipe:
                user_recipes.append(recipe)
        
        user_recipe_ids_set = set(user_recipe_ids)
        # Load fresh recipe data for each ID (to get current likes)
        latest_recipes = []
        for recipe_id in latest_recipe_ids:
            if recipe_id not in user_recipe_ids_set:
                recipe = _load_recipe_raw(recipe_id)
                if recipe:
                    latest_recipes.append(recipe)
        
        combined = user_recipes + latest_recipes
    else:
        # Load fresh recipe data for each ID
        combined = []
        for recipe_id in latest_recipe_ids:
            recipe = _load_recipe_raw(recipe_id)
            if recipe:
                combined.append(recipe)
    
    result = [_apply_recipe_filters(r, current_user) for r in combined]
    
    return result


def get_recipe_by_id(recipe_id: str, current_user: Optional[str] = None) -> Optional[Dict]:
    _ensure_recipes_dir()
    
    recipe = _load_recipe_raw(recipe_id)
    if not recipe:
        return None
    
    return _apply_recipe_filters(recipe, current_user)


def like_recipe(recipe_id: str, user: str) -> Dict:
    _ensure_recipes_dir()
    
    recipe_path = os.path.join(RECIPES_DIR, f"{recipe_id}.json")
    if not os.path.exists(recipe_path):
        return {"error": "Recipe not found"}
    
    try:
        with open(recipe_path, "r") as f:
            recipe = json.load(f)
        
        if "likes" not in recipe:
            recipe["likes"] = 0
        if "liked_by" not in recipe:
            recipe["liked_by"] = []
        
        if user in recipe["liked_by"]:
            return {"error": "Already liked"}
        
        recipe["likes"] += 1
        recipe["liked_by"].append(user)
        
        with open(recipe_path, "w") as f:
            json.dump(recipe, f, indent=2)
        
        return {"status": "success", "likes": recipe["likes"]}
    
    except (json.JSONDecodeError, KeyError) as e:
        return {"error": f"Failed to update recipe: {str(e)}"}


# Auto-start cache refresh on module import
start_cache_refresh()
