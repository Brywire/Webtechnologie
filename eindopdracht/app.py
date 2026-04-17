from flask import Flask

from extensions import db, login_manager
from models import User
from routes import register_routes

app = Flask(__name__)
app.config["SECRET_KEY"] = "geheim-sleutel-verander-dit-later"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///studyflow.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Log eerst in om je taken te bekijken."
login_manager.login_message_category = "error"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


register_routes(app)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)