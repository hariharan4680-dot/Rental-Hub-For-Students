from flask import Flask, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Flask app (HTML in templates/, CSS/JS in static/)
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# Secret key for JWT or session usage
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your-secret-key")

# ✅ Import routes after initializing app
from routes.auth_routes import auth_routes
from routes.rent_routes import rent_routes
from routes.bookings_routes import bookings_routes

# Register API routes
app.register_blueprint(auth_routes, url_prefix="/api")
app.register_blueprint(rent_routes, url_prefix="/api")
app.register_blueprint(bookings_routes, url_prefix="/api")


# ✅ Root route → landing page
@app.route("/")
def landing():
    return render_template("index.html")  # change to login.html if preferred

# ✅ Auth pages
@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

# ✅ Dashboard page
@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

# ✅ Post Rent page (form UI only, API is in rent_routes)
@app.route("/post-rent")
def post_rent_page():
    return render_template("post_rent.html")

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ✅ Update Profile page
@app.route("/update-profile")
def update_profile_page():
    return render_template("update_profile.html")


# Run app
if __name__ == "__main__":
    app.run(debug=True)
