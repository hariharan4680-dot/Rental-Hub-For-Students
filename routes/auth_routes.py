from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import os
from db import db
from utils.token_required import token_required

auth_routes = Blueprint('auth', __name__)

# ✅ Register a new student
@auth_routes.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if db.students.find_one({"email": data["email"]}):
        return jsonify({"error": "Email already exists"}), 400

    hashed_password = generate_password_hash(data["password"])
    db.students.insert_one({
        "name": data["name"],
        "email": data["email"],
        "password": hashed_password
    })
    return jsonify({"message": "Registration successful"}), 201


# ✅ Login and return JWT token
@auth_routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = db.students.find_one({"email": data["email"]})
    if not user or not check_password_hash(user["password"], data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode({
        "email": user["email"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }, os.getenv("JWT_SECRET"), algorithm="HS256")

    return jsonify({"message": "Login successful", "token": token})


# ✅ View profile with rental posts
@auth_routes.route('/profile', methods=['GET'])
@token_required
def profile(current_user):
    user = db.students.find_one({"email": current_user}, {"_id": 0, "password": 0})
    if not user:
        return jsonify({"error": "User not found"}), 404

    posts = list(db.rentals.find({"email": current_user}))
    for post in posts:
        post["_id"] = str(post["_id"])

    return jsonify({
        "user": user,
        "rentals": posts
    })


# ✅ Update profile (name, email, password)
@auth_routes.route('/update-profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    data = request.get_json()
    update_data = {}

    # allow name update
    if "name" in data and data["name"].strip():
        update_data["name"] = data["name"].strip()

    # allow email update (check uniqueness)
    if "email" in data and data["email"].strip():
        existing = db.students.find_one({"email": data["email"]})
        if existing and existing["email"] != current_user:
            return jsonify({"error": "Email already in use"}), 400
        update_data["email"] = data["email"].strip()

    # allow password update
    if "password" in data and data["password"].strip():
        update_data["password"] = generate_password_hash(data["password"])

    if not update_data:
        return jsonify({"error": "No valid fields to update"}), 400

    result = db.students.update_one(
        {"email": current_user},
        {"$set": update_data}
    )

    if result.modified_count == 1:
        return jsonify({"message": "Profile updated successfully!"}), 200
    else:
        return jsonify({"message": "No changes made."}), 200
