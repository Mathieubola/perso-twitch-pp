from flask import Flask, redirect, request, url_for, render_template, send_file
from flask_dance.contrib.twitch import make_twitch_blueprint, twitch

import json
from os import getenv, path, listdir
from dotenv import load_dotenv
load_dotenv()

address = getenv("ADDRESS")
static_folder = getenv("STATIC_FOLDER")
duck_folder = path.join(static_folder, "duck_images")

app = Flask(__name__, static_folder=static_folder)
app.secret_key = getenv("SECRET_KEY")

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
    if not twitch.authorized:
        return render_template("index.html", url=url_for("twitch.login"))
    else:
        return redirect(url_for("choose_image"))

# Image upload endpoint
@app.route('/choose', methods=['GET', 'POST'])
def choose_image():
    if not twitch.authorized:
        return redirect(url_for("twitch.login"))
    else:
        user_info = twitch.get("/helix/users").json()
        twitch_username = user_info["data"][0]["login"].lower()

        choices = listdir(duck_folder)
        choices = [
            path.join(duck_folder, choice)
            for choice in choices
            if choice.endswith(".png") or choice.endswith(".jpg")]

        if request.method == 'GET':
            return render_template("choose.html", images=choices, username=twitch_username)
        else:
            choice = request.form.get('canard', -1)

            if choice == -1:
                return "No image selected " + str(request.form)

            with open("./data/choices.json", 'r') as f:
                datas_tream = json.load(f)

            datas_tream[twitch_username] = choice

            with open("./data/choices.json", 'w') as f:
                json.dump(datas_tream, f)

            return render_template("choose.html", images=choices, username=twitch_username, message="Image choisie !")

# Image retrieval endpoint
@app.route('/img/<twitch_username>/<idc>')
@app.route('/img/<twitch_username>')
def get_image(twitch_username, idc=None):
    with open("./data/choices.json", 'r') as f:
        choices = json.load(f)

    choice = choices.get(twitch_username.lower(), path.join(duck_folder, "Sans_titre.jpg"))
    return send_file(choice)

if __name__ == '__main__':
    app.run(port=5000, host="0.0.0.0")
