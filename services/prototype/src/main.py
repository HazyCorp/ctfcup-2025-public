import flask
from flask import request, g, jsonify, send_from_directory
from connectors.minio_connector import create_account, upload_file_to_publish
from authenticator.token_validator import saltify, unsaltify, SALT
from storage.recipes_storage import publish_recipe, get_recipes, like_recipe
import uuid
import hashlib

app = flask.Flask(__name__, static_folder='static', static_url_path='/static')


@app.before_request
def before_request():
    try:
        g.user, g.passwd = unsaltify(request.headers.get("X-Token")).split(":")
    except Exception as e:
        pass

@app.get("/obtain_account")
def obtain_account():
    user, passwd = create_account()
    return saltify(f"{user}:{passwd}")

@app.get("/salt_hash")
def get_salt_hash():
    salt_hash = hashlib.sha256(SALT.encode()).hexdigest()
    return jsonify({"salt_hash": salt_hash}), 200

@app.post("/upload")
def upload():
    if not hasattr(g, 'user') or not g.user:
        return jsonify({"error": "Authentication required"}), 401
    
    if "file" not in request.files:
        return jsonify({"error": "No file in request"}), 400

    file = request.files["file"]
    file_bytes = file.read(1025)
    
    if len(file_bytes) > 1024:
        return jsonify({"error": "File size exceeds 1KB limit"}), 400
    
    filename = f"preview_{uuid.uuid4().hex[:12]}"
    location = upload_file_to_publish(g.user, g.passwd, filename, file_bytes[:1024])

    return jsonify({"status": "success", "loc": location}), 200

@app.post("/publish_recipe")
def publish_recipe_endpoint():
    if not hasattr(g, 'user') or not g.user:
        return jsonify({"error": "Authentication required"}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    
    recipe_text = data.get("recipe_text")
    secret_ingredient = data.get("secret_ingredient")
    preview_location = data.get("preview_location")
    
    if not recipe_text or not secret_ingredient or not preview_location:
        return jsonify({"error": "Missing required fields: recipe_text, secret_ingredient, preview_location"}), 400
    
    try:
        recipe_id = publish_recipe(g.user, recipe_text, secret_ingredient, preview_location)
        return jsonify({"status": "success", "recipe_id": recipe_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/recipes")
def get_recipes_endpoint():
    current_user = getattr(g, 'user', None)
    
    try:
        recipes = get_recipes(current_user)
        
        for recipe in recipes:
            preview_location = recipe.get("preview_location", "")
            if preview_location:
                recipe["preview_url"] = f"s3/{preview_location}"
            else:
                recipe["preview_url"] = None
        
        return jsonify({"recipes": recipes}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.put("/like_recipe")
def like_recipe_endpoint():
    if not hasattr(g, 'user') or not g.user:
        return jsonify({"error": "Authentication required"}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    
    recipe_id = data.get("recipe_id")
    if not recipe_id:
        return jsonify({"error": "Missing recipe_id"}), 400
    
    try:
        result = like_recipe(recipe_id, g.user)
        
        if "error" in result:
            return jsonify(result), 400
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/")
def index():
    return send_from_directory('static', 'index.html')


@app.get("/health")
def health():
    return jsonify({"status": "healthy"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
