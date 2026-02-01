# src/app.py
"""
This module starts the API server, loads the DB and exposes endpoints.
Designed to work with the models you already created (User, People, Planet, Favorite).
"""
import os
import secrets
from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_cors import CORS

from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planet, Favorite

app = Flask(__name__)
app.url_map.strict_slashes = False

# SECRET KEY -> necesaria para sesiones y flash (Flask-Admin)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)

# Database config
db_url = os.getenv("DATABASE_URL")
if db_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Init extensions (orden importante)
db.init_app(app)
MIGRATE = Migrate(app, db)
CORS(app)
setup_admin(app)   # registra vistas admin una vez DB inicializada

# ---------- Error handler ----------
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# ---------- Sitemap / health ----------
@app.route('/')
def sitemap():
    return generate_sitemap(app)

# ---------- PEOPLE endpoints ----------
@app.route('/people', methods=['GET'])
def get_all_people():
    people = People.query.all()
    result = [p.serialize() for p in people]
    return jsonify(result), 200


@app.route('/people/<int:people_id>', methods=['GET'])
def get_one_people(people_id):
    person = People.query.filter_by(id=people_id).first()
    if person is None:
        raise APIException("People not found", status_code=404)
    return jsonify(person.serialize()), 200

# ---------- PLANETS endpoints ----------
@app.route('/planets', methods=['GET'])
def get_all_planets():
    planets = Planet.query.all()
    result = [p.serialize() for p in planets]
    return jsonify(result), 200


@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_one_planet(planet_id):
    planet = Planet.query.filter_by(id=planet_id).first()
    if planet is None:
        raise APIException("Planet not found", status_code=404)
    return jsonify(planet.serialize()), 200

# ---------- USERS endpoints ----------
@app.route('/users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    result = [u.serialize() for u in users]
    return jsonify(result), 200

# Hardcoded current user (scope/simulacion)
CURRENT_USER_ID = 1

@app.route('/users/favorites', methods=['GET'])
def get_current_user_favorites():
    user = User.query.filter_by(id=CURRENT_USER_ID).first()
    if user is None:
        raise APIException("Current user not found", status_code=404)

    favorites = Favorite.query.filter_by(user_id=CURRENT_USER_ID).all()
    result = []
    for f in favorites:
        item = {
            "id": f.id,
            "people_id": f.people_id,
            "planet_id": f.planet_id,
        }
        if f.people is not None:
            item["people"] = f.people.serialize()
        if f.planet is not None:
            item["planet"] = f.planet.serialize()
        result.append(item)

    return jsonify(result), 200

# ---------- FAVORITES: add / remove ----------
@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    user = User.query.filter_by(id=CURRENT_USER_ID).first()
    if user is None:
        raise APIException("Current user not found", status_code=404)

    planet = Planet.query.filter_by(id=planet_id).first()
    if planet is None:
        raise APIException("Planet not found", status_code=404)

    existing = Favorite.query.filter_by(user_id=CURRENT_USER_ID, planet_id=planet_id).first()
    if existing:
        raise APIException("Favorite already exists", status_code=400)

    fav = Favorite(user_id=CURRENT_USER_ID, planet_id=planet_id)
    db.session.add(fav)
    db.session.commit()

    return jsonify({"message": "Favorite added", "favorite": fav.serialize()}), 201


@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_people(people_id):
    user = User.query.filter_by(id=CURRENT_USER_ID).first()
    if user is None:
        raise APIException("Current user not found", status_code=404)

    person = People.query.filter_by(id=people_id).first()
    if person is None:
        raise APIException("People not found", status_code=404)

    existing = Favorite.query.filter_by(user_id=CURRENT_USER_ID, people_id=people_id).first()
    if existing:
        raise APIException("Favorite already exists", status_code=400)

    fav = Favorite(user_id=CURRENT_USER_ID, people_id=people_id)
    db.session.add(fav)
    db.session.commit()

    return jsonify({"message": "Favorite added", "favorite": fav.serialize()}), 201


@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    fav = Favorite.query.filter_by(user_id=CURRENT_USER_ID, planet_id=planet_id).first()
    if fav is None:
        raise APIException("Favorite not found", status_code=404)

    db.session.delete(fav)
    db.session.commit()
    return jsonify({"message": "Favorite removed", "planet_id": planet_id}), 200


@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_people(people_id):
    fav = Favorite.query.filter_by(user_id=CURRENT_USER_ID, people_id=people_id).first()
    if fav is None:
        raise APIException("Favorite not found", status_code=404)

    db.session.delete(fav)
    db.session.commit()
    return jsonify({"message": "Favorite removed", "people_id": people_id}), 200


# ---------- Run server ----------
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
