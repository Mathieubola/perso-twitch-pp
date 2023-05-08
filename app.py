from flask import Flask, redirect, request, url_for, render_template, send_file
from flask_dance.contrib.twitch import make_twitch_blueprint, twitch

import json
from os import getenv, path, listdir
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, static_folder=getenv('UPLOAD_FOLDER'))
app.secret_key = getenv("SECRET_KEY")

address = getenv("ADDRESS")
image_folder = getenv("UPLOAD_FOLDER")

# Set up Twitch authentication
twitch_blueprint = make_twitch_blueprint(
    client_id=getenv("TWITCH_CLIENT_ID"),
    client_secret=getenv("TWITCH_CLIENT_SECRET"),
    redirect_url=address,
    scope=["user:read:email"]
)
app.register_blueprint(twitch_blueprint, url_prefix="/login")

# Index endpoint
@app.route('/')
def index():
    print("Index:", twitch.authorized)
    if not twitch.authorized:
        return render_template("index.html", url=url_for("twitch.login"))
    else:
        return redirect(url_for("choose_image"))

# Image upload endpoint
@app.route('/choose', methods=['GET', 'POST'])
def choose_image():
    print("Choose:", twitch.authorized)
    if not twitch.authorized:
        return redirect(url_for("twitch.login"))
    else:
        user_info = twitch.get("/helix/users").json()
        twitch_username = user_info["data"][0]["login"].lower()
        if request.method == 'GET':
            choices = listdir(getenv('UPLOAD_FOLDER'))
            choices = [
                path.join(image_folder, choice)
                for choice in choices
                if choice.endswith(".png") or choice.endswith(".jpg")]
            return render_template("choose.html", images=choices, username=twitch_username)
        else:
            choice = request.form.get('image', -1)
            print("Choice:", choice)

            if choice == -1:
                return "No image selected"

            with open("./data/choices.json", 'r') as f:
                choices = json.load(f)

            choices[twitch_username] = choice

            with open("./data/choices.json", 'w') as f:
                json.dump(choices, f)

            return "Image selected"

# Image retrieval endpoint
@app.route('/img/<twitch_username>')
def get_image(twitch_username):
    with open("./data/choices.json", 'r') as f:
        choices = json.load(f)
    
    print(twitch_username)

    choice = choices.get(twitch_username.lower(), "images/Sans_titre.jpg")
    return send_file(choice)

if __name__ == '__main__':
    app.run(debug=True, port=5000, host="0.0.0.0")