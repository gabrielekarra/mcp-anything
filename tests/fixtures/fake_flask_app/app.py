"""Fake Flask app for testing route extraction."""

from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/users", methods=["GET"])
def list_users():
    """List all users."""
    return jsonify([])


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    """Get a user by ID."""
    return jsonify({"id": user_id})


@app.route("/users", methods=["POST"])
def create_user():
    """Create a new user."""
    data = request.json
    return jsonify({"id": 1}), 201


@app.route("/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    """Delete a user."""
    return jsonify({"deleted": True})


@app.route("/health")
def health():
    """Health check."""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(port=5000)
