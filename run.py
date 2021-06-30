import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.config["VIDEO_UPLOADS"] = "/workspace/youth-space/static/videos"
app.config["ALLOWED_VIDEO_EXTENSIONS"] = ["MP4", "MOV", "GIF"]
app.config["MAX_VIDEO-FILESIZE"] = 10000000

app.secret_key = os.environ.get("SECRET_KEY")


mongo = PyMongo(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/get_videos")
def get_videos():
    videos = list(mongo.db.videos.find())
    return render_template("videos.html", videos=videos)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in database
        existing_user = mongo.db.users.find_one(
             {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Sorry...username already taken!")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password")),
            "first_name": request.form.get("first_name").lower(),
            "last_name": request.form.get("last_name").lower()
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Your registration is complete!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                        session["user"] = request.form.get("username").lower()
                        flash("Welcome, {}".format(
                            request.form.get("username")))
                        return redirect(url_for(
                            "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect username and/or Password")
                return redirect(url_for("signin"))

        else:
            # username doesn't exist
            flash("Incorrect username and/or Password")
            return redirect(url_for("signin"))

    return render_template("signin.html")


@app.route("/profile<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("signin"))


@app.route("/signout")
def signout():
    # remove user from session coikes
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("signin"))


def allowed_video(filename):
    if not "." in filename:
        return False
    ext = filename.rsplit(".", 1)[1]
    if ext.upper() in app.config["ALLOWED_VIDEO_EXTENSIONS"]:
        return True
    else:
        return False


def allowed_video_filesize(filesize):

    if int(filesize) <= app.config["MAX_VIDEO-FILESIZE"]:
        return True
    else:
        return False


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if request.files:
            if not allowed_video_filesize(request.cookies.get("filesize")):
                flash("File exceeded maximum size")
                return redirect(request.url)
            video = request.files["video"]
            if video.filename == "":
                flash("video must have a filename")
                return redirect(request.url)
            # If the video format is not MP4, MOV, or GIF
            if not allowed_video(video.filename):
                flash("That video extension is not allowed")
                return redirect(request.url)
            else:
                filename = secure_filename(video.filename) 
                video.save(os.path.join(
                app.config["VIDEO_UPLOADS"], filename))
            flash("video loaded")
            return redirect(request.url)
    return render_template("upload.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
