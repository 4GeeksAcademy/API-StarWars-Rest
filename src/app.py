# src/app.py
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

app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)

db_url = os.getenv("DATABASE_URL")
if db_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
MIGRATE = Migrate(app, db)
CORS(app)
setup_admin(app)

@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

@app.route('/')
def sitemap():
    return generate_sitemap(app)

# People endpoints
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

@app.route('/people', methods=['POST'])
def create_people():
    body = request.get_json(force=True)
    name = body.get("name")
    if not name:
        raise APIException("Missing required field: name", status_code=400)
    gender = body.get("gender")
    birth_year = body.get("birth_year")
    new_person = People(name=name, gender=gender, birth_year=birth_year)
    db.session.add(new_person)
    db.session.commit()
    return jsonify(new_person.serialize()), 201

@app.route('/people/<int:people_id>', methods=['PUT'])
def update_people(people_id):
    person = People.query.filter_by(id=people_id).first()
    if person is None:
        raise APIException("People not found", status_code=404)
    body = request.get_json(force=True)
    name = body.get("name")
    gender = body.get("gender")
    birth_year = body.get("birth_year")
    if name is not None:
        if not str(name).strip():
            raise APIException("Invalid name", status_code=400)
        person.name = name
    if gender is not None:
        person.gender = gender
    if birth_year is not None:
        person.birth_year = birth_year
    db.session.commit()
    return jsonify(person.serialize()), 200

@app.route('/people/<int:people_id>', methods=['DELETE'])
def delete_people(people_id):
    person = People.query.filter_by(id=people_id).first()
    if person is None:
        raise APIException("People not found", status_code=404)
    Favorite.query.filter_by(people_id=people_id).delete()
    db.session.delete(person)
    db.session.commit()
    return jsonify({"message": "People deleted", "people_id": people_id}), 200

# Planet endpoints
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

@app.route('/planets', methods=['POST'])
def create_planet():
    body = request.get_json(force=True)
    name = body.get("name")
    if not name:
        raise APIException("Missing required field: name", status_code=400)
    climate = body.get("climate")
    population = body.get("population")
    new_planet = Planet(name=name, climate=climate, population=population)
    db.session.add(new_planet)
    db.session.commit()
    return jsonify(new_planet.serialize()), 201

@app.route('/planets/<int:planet_id>', methods=['PUT'])
def update_planet(planet_id):
    planet = Planet.query.filter_by(id=planet_id).first()
    if planet is None:
        raise APIException("Planet not found", status_code=404)
    body = request.get_json(force=True)
    name = body.get("name")
    climate = body.get("climate")
    population = body.get("population")
    if name is not None:
        if not str(name).strip():
            raise APIException("Invalid name", status_code=400)
        planet.name = name
    if climate is not None:
        planet.climate = climate
    if population is not None:
        planet.population = population
    db.session.commit()
    return jsonify(planet.serialize()), 200

@app.route('/planets/<int:planet_id>', methods=['DELETE'])
def delete_planet(planet_id):
    planet = Planet.query.filter_by(id=planet_id).first()
    if planet is None:
        raise APIException("Planet not found", status_code=404)
    Favorite.query.filter_by(planet_id=planet_id).delete()
    db.session.delete(planet)
    db.session.commit()
    return jsonify({"message": "Planet deleted", "planet_id": planet_id}), 200

# Users endpoints
@app.route('/users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    result = [u.serialize() for u in users]
    return jsonify(result), 200

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

# Favorites add/remove
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

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
