from flask import Blueprint, request, jsonify
from db import db
from utils.token_required import token_required
from bson import ObjectId
from datetime import datetime
from werkzeug.utils import secure_filename
import os

rent_routes = Blueprint('rentals', __name__)

# Folder for storing uploaded images
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ------------------ POST /post-rent (with image upload) ------------------
@rent_routes.route('/post-rent', methods=['POST'])
@token_required
def post_rent(current_user):
    try:
        # For image upload, use form-data instead of raw JSON
        title = request.form.get("title")
        description = request.form.get("description")
        price = request.form.get("price")
        location = request.form.get("location")
        category = request.form.get("category", "room")
        image_file = request.files.get("image")

        # Save image if provided
        image_path = None
        if image_file:
            filename = secure_filename(image_file.filename)
            image_save_path = os.path.join(UPLOAD_FOLDER, filename)
            image_file.save(image_save_path)
            # Make accessible path for frontend
            image_path = "/" + image_save_path.replace("\\", "/")

        # Convert price safely
        try:
            price = int(price)
        except (TypeError, ValueError):
            price = 0

        rent_post = {
            "title": title,
            "description": description,
            "price": price,
            "location": location,
            "category": category,
            "email": current_user,
            "image": image_path,
            "created_at": datetime.utcnow()
        }

        db.rentals.insert_one(rent_post)
        return jsonify({"message": "Rental posted successfully!", "image": image_path}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------ GET /my-posts ------------------
@rent_routes.route('/my-posts', methods=['GET'])
@token_required
def my_posts(current_user):
    posts = list(db.rentals.find({"email": current_user}).sort("created_at", -1))
    for post in posts:
        post["_id"] = str(post["_id"])
    return jsonify(posts), 200


# ------------------ GET /all-posts (pagination) ------------------
@rent_routes.route('/all-posts', methods=['GET'])
def all_posts():
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return jsonify({"error": "Invalid pagination values"}), 400

    if page < 1 or limit < 1:
        return jsonify({"error": "Page and limit must be positive"}), 400

    sort_by = request.args.get("sort_by", "created_at")
    order = request.args.get("order", "desc")
    sort_order = -1 if order == "desc" else 1
    allowed_sort_fields = ["created_at", "price", "title", "location", "category"]

    if sort_by not in allowed_sort_fields:
        return jsonify({"error": f"Invalid sort_by field. Allowed: {allowed_sort_fields}"}), 400

    total_count = db.rentals.count_documents({})
    posts = db.rentals.find({}).sort(sort_by, sort_order).skip((page - 1) * limit).limit(limit)

    posts_list = []
    for post in posts:
        post["_id"] = str(post["_id"])
        posts_list.append(post)

    return jsonify({
        "success": True,
        "count": len(posts_list),
        "total": total_count,
        "page": page,
        "limit": limit,
        "results": posts_list
    }), 200


# ------------------ PUT /edit-post/<post_id> ------------------
@rent_routes.route('/edit-post/<post_id>', methods=['PUT'])
@token_required
def edit_post(current_user, post_id):
    try:
        data = request.get_json()
        if not ObjectId.is_valid(post_id):
            return jsonify({"error": "Invalid post_id"}), 400

        post = db.rentals.find_one({"_id": ObjectId(post_id)})
        if not post:
            return jsonify({"error": "Post not found"}), 404
        if post["email"] != current_user:
            return jsonify({"error": "Unauthorized"}), 403

        update_data = {
            "title": data.get("title", post["title"]),
            "description": data.get("description", post["description"]),
            "location": data.get("location", post["location"]),
            "category": data.get("category", post.get("category", "room"))
        }

        if "price" in data and data.get("price") != "":
            try:
                update_data["price"] = int(data["price"])
            except ValueError:
                return jsonify({"error": "Invalid price"}), 400

        db.rentals.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": update_data}
        )

        return jsonify({"message": "Post updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------ DELETE /delete-post/<post_id> ------------------
@rent_routes.route('/delete-post/<post_id>', methods=['DELETE'])
@token_required
def delete_post(current_user, post_id):
    try:
        if not ObjectId.is_valid(post_id):
            return jsonify({"error": "Invalid post_id"}), 400

        post = db.rentals.find_one({"_id": ObjectId(post_id)})
        if not post:
            return jsonify({"error": "Post not found"}), 404
        if post["email"] != current_user:
            return jsonify({"error": "Unauthorized"}), 403

        db.rentals.delete_one({"_id": ObjectId(post_id)})
        return jsonify({"message": "Post deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------ GET /search (pagination + filters) ------------------
@rent_routes.route("/search", methods=["GET"])
def search_posts():
    title = request.args.get("title")
    location = request.args.get("location")
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")
    category = request.args.get("category")

    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return jsonify({"error": "Invalid pagination values"}), 400

    if page < 1 or limit < 1:
        return jsonify({"error": "Page and limit must be positive"}), 400

    sort_by = request.args.get("sort_by", "created_at")
    order = request.args.get("order", "desc")
    sort_order = -1 if order == "desc" else 1
    allowed_sort_fields = ["created_at", "price", "title", "location", "category"]

    if sort_by not in allowed_sort_fields:
        return jsonify({"error": f"Invalid sort_by field. Allowed: {allowed_sort_fields}"}), 400

    # Build query filters
    query = {}
    if title:
        query["title"] = {"$regex": title, "$options": "i"}
    if location:
        query["location"] = {"$regex": location, "$options": "i"}
    if min_price or max_price:
        price_filter = {}
        if min_price:
            try:
                price_filter["$gte"] = int(min_price)
            except ValueError:
                return jsonify({"error": "Invalid min_price"}), 400
        if max_price:
            try:
                price_filter["$lte"] = int(max_price)
            except ValueError:
                return jsonify({"error": "Invalid max_price"}), 400
        query["price"] = price_filter
    if category:
        query["category"] = category

    total_count = db.rentals.count_documents(query)
    posts = db.rentals.find(query).sort(sort_by, sort_order).skip((page - 1) * limit).limit(limit)

    posts_list = []
    for post in posts:
        post["_id"] = str(post["_id"])
        posts_list.append(post)

    return jsonify({
        "success": True,
        "count": len(posts_list),
        "total": total_count,
        "page": page,
        "limit": limit,
        "results": posts_list
    }), 200
