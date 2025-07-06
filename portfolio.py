from flask import Blueprint, jsonify, session

portfolio_bp = Blueprint("portfolio", __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "access_token" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

@portfolio_bp.route("/portfolio", methods=["GET"])
@login_required
def get_portfolio():
    # Example static response; replace with DB query
    return jsonify({
        "message": f"Portfolio for {session['username']}",
        "stocks": []
    })

@portfolio_bp.route("/add_stock", methods=["POST"])
@login_required
def add_stock():
    # Example placeholder
    return jsonify({"message": "Add stock endpoint"})
