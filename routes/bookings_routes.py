from flask import Blueprint, request, jsonify
from db import db
from utils.token_required import token_required
from bson import ObjectId
import datetime

bookings_routes = Blueprint("bookings", __name__)

# Helper to serialize booking documents
def _serialize_booking(b):
    return {
        "_id": str(b.get("_id")),
        "post_id": str(b.get("post_id")),
        "post_title": b.get("post_title"),
        "owner_email": b.get("owner_email"),
        "renter_email": b.get("renter_email"),
        "start_date": b.get("start_date").date().isoformat() if isinstance(b.get("start_date"), datetime.datetime) else str(b.get("start_date")),
        "end_date": b.get("end_date").date().isoformat() if isinstance(b.get("end_date"), datetime.datetime) else str(b.get("end_date")),
        "message": b.get("message"),
        "status": b.get("status"),
        "created_at": b.get("created_at").isoformat() if b.get("created_at") else None
    }

# POST /api/book
@bookings_routes.route("/book", methods=["POST"])
@token_required
def create_booking(current_user):
    if db is None:
        return jsonify({"error": "DB not connected"}), 500

    data = request.get_json() or {}
    post_id = data.get("post_id")
    start = data.get("start_date")
    end = data.get("end_date")
    message = data.get("message", "")

    if not post_id or not start or not end:
        return jsonify({"error": "post_id, start_date and end_date are required"}), 400

    # validate date format (expect YYYY-MM-DD)
    try:
        start_dt = datetime.datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.datetime.strptime(end, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Dates must be in YYYY-MM-DD format"}), 400

    if end_dt < start_dt:
        return jsonify({"error": "end_date must be on or after start_date"}), 400

    # Get post
    try:
        post = db.rentals.find_one({"_id": ObjectId(post_id)})
    except Exception:
        return jsonify({"error": "Invalid post_id"}), 400

    if not post:
        return jsonify({"error": "Post not found"}), 404

    owner_email = post.get("email")
    renter_email = current_user

    if owner_email == renter_email:
        return jsonify({"error": "You cannot book your own post"}), 403

    # Check for conflicting accepted bookings
    conflict = db.bookings.find_one({
        "post_id": ObjectId(post_id),
        "status": "accepted",
        "$or": [
            { "start_date": { "$lte": end_dt }, "end_date": { "$gte": start_dt } }
        ]
    })
    if conflict:
        return jsonify({"error": "Dates conflict with an existing booking"}), 409

    booking_doc = {
        "post_id": ObjectId(post_id),
        "post_title": post.get("title"),
        "owner_email": owner_email,
        "renter_email": renter_email,
        "start_date": start_dt,
        "end_date": end_dt,
        "message": message,
        "status": "pending",
        "created_at": datetime.datetime.utcnow()
    }

    res = db.bookings.insert_one(booking_doc)
    booking_doc["_id"] = str(res.inserted_id)
    return jsonify({"message": "Booking request created", "booking": _serialize_booking(booking_doc)}), 201


# GET /api/my-bookings  (renter)
@bookings_routes.route("/my-bookings", methods=["GET"])
@token_required
def my_bookings(current_user):
    if db is None:
        return jsonify({"error": "DB not connected"}), 500
    docs = list(db.bookings.find({"renter_email": current_user}).sort("created_at", -1))
    return jsonify([_serialize_booking(d) for d in docs])


# GET /api/owner-bookings  (owner incoming requests)
@bookings_routes.route("/owner-bookings", methods=["GET"])
@token_required
def owner_bookings(current_user):
    if db is None:
        return jsonify({"error": "DB not connected"}), 500
    docs = list(db.bookings.find({"owner_email": current_user}).sort("created_at", -1))
    return jsonify([_serialize_booking(d) for d in docs])


# PUT /api/bookings/<booking_id>/status  (owner accepts/rejects)
@bookings_routes.route("/bookings/<booking_id>/status", methods=["PUT"])
@token_required
def update_booking_status(current_user, booking_id):
    if db is None:
        return jsonify({"error": "DB not connected"}), 500

    data = request.get_json() or {}
    new_status = data.get("status")
    if new_status not in ("accepted", "rejected"):
        return jsonify({"error": "Status must be 'accepted' or 'rejected'"}), 400

    try:
        booking = db.bookings.find_one({"_id": ObjectId(booking_id)})
    except Exception:
        return jsonify({"error": "Invalid booking id"}), 400

    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    if booking.get("owner_email") != current_user:
        return jsonify({"error": "Only the owner can update booking status"}), 403

    # If accepting, double-check there's no accepted conflict
    if new_status == "accepted":
        start_dt = booking.get("start_date")
        end_dt = booking.get("end_date")
        conflict = db.bookings.find_one({
            "post_id": booking.get("post_id"),
            "status": "accepted",
            "_id": {"$ne": booking.get("_id")},
            "$or": [
                { "start_date": { "$lte": end_dt }, "end_date": { "$gte": start_dt } }
            ]
        })
        if conflict:
            return jsonify({"error": "Cannot accept: dates conflict with another accepted booking"}), 409

    db.bookings.update_one({"_id": booking.get("_id")}, {"$set": {"status": new_status}})
    return jsonify({"message": f"Booking {new_status}"})


# DELETE /api/bookings/<booking_id> (renter cancels)
@bookings_routes.route("/bookings/<booking_id>", methods=["DELETE"])
@token_required
def cancel_booking(current_user, booking_id):
    if db is None:
        return jsonify({"error": "DB not connected"}), 500

    try:
        booking = db.bookings.find_one({"_id": ObjectId(booking_id)})
    except Exception:
        return jsonify({"error": "Invalid booking id"}), 400

    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    if booking.get("renter_email") != current_user:
        return jsonify({"error": "Only the renter can cancel this booking"}), 403

    # either delete or mark cancelled — we will mark cancelled
    db.bookings.update_one({"_id": booking.get("_id")}, {"$set": {"status": "cancelled"}})
    return jsonify({"message": "Booking cancelled"})
