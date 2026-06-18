# utils/token_required.py
from functools import wraps
from flask import request, jsonify
import jwt
import os

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth:
            return jsonify({"error": "Token is missing"}), 401

        parts = auth.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Token must be in format: 'Bearer <token>'"}), 401

        token = parts[1]
        secret = os.getenv("JWT_SECRET")
        if not secret:
            return jsonify({"error": "Server misconfiguration: JWT_SECRET missing"}), 500

        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            current_user = payload.get("email")
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token is invalid!"}), 401

        # passes current_user (email) into the protected route
        return f(current_user, *args, **kwargs)

    return decorated
