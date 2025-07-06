from flask import Flask, render_template, request, redirect, session, url_for
import boto3

app = Flask(__name__)
app.secret_key = "super-secret-key"  # Change this to a strong random key

# Your AWS Cognito config
COGNITO_CLIENT_ID = "<YOUR_CLIENT_ID>"
COGNITO_USER_POOL_ID = "<YOUR_USER_POOL_ID>"
COGNITO_REGION = "ap-south-1"

cognito = boto3.client("cognito-idp", region_name=COGNITO_REGION)

@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("profile"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        try:
            cognito.sign_up(
                ClientId=COGNITO_CLIENT_ID,
                Username=username,
                Password=password,
                UserAttributes=[
                    {"Name": "email", "Value": email}
                ]
            )
            return (
                "✅ Registration successful. Please check your email to confirm the account.<br>"
                "<a href='/login'>Go to login</a>"
            )
        except Exception as e:
            return f"❌ Registration error: {str(e)}"
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        try:
            resp = cognito.initiate_auth(
                ClientId=COGNITO_CLIENT_ID,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": username,
                    "PASSWORD": password
                }
            )
            session["username"] = username
            session["access_token"] = resp["AuthenticationResult"]["AccessToken"]
            return redirect(url_for("profile"))
        except Exception as e:
            return f"❌ Login error: {str(e)}"
    return render_template("login.html")

@app.route("/profile")
def profile():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("profile.html", username=session["username"])

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
