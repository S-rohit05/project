from flask import Blueprint, request, jsonify, session
import boto3
import hmac
import hashlib
import base64

auth_bp = Blueprint("auth", __name__)

# Cognito config
COGNITO_REGION = "ap-south-1"
COGNITO_USER_POOL_ID = "YOUR_USER_POOL_ID"
COGNITO_CLIENT_ID = "YOUR_CLIENT_ID"
COGNITO_CLIENT_SECRET = "YOUR_CLIENT_SECRET"

client = boto3.client("cognito-idp", region_name=COGNITO_REGION)

def get_secret_hash(username):
    message = username + COGNITO_CLIENT_ID
    dig = hmac.new(
        key=COGNITO_CLIENT_SECRET.encode('utf-8'),
        msg=message.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json
    try:
        client.sign_up(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=get_secret_hash(data["username"]),
            Username=data["username"],
            Password=data["password"],
            UserAttributes=[
                {"Name": "email", "Value": data["email"]}
            ]
        )
        return jsonify({"message": "User registered. Please confirm email if required."})
    except client.exceptions.UsernameExistsException:
        return jsonify({"error": "Username already exists"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    try:
        response = client.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": data["username"],
                "PASSWORD": data["password"],
                "SECRET_HASH": get_secret_hash(data["username"])
            }
        )
        session["username"] = data["username"]
        session["access_token"] = response["AuthenticationResult"]["AccessToken"]
        return jsonify({"message": "Login successful"})
    except client.exceptions.NotAuthorizedException:
        return jsonify({"error": "Incorrect username or password"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})
