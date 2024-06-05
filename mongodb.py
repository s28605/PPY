from flask_pymongo import PyMongo
from bson import ObjectId

mongo = None


def init_app(app):
    global mongo
    mongo = PyMongo(app)
    return mongo


def find_user_by_id(user_id):
    return mongo.db.users.find_one({"_id": ObjectId(user_id)})


def find_user_by_username(username):
    return mongo.db.users.find_one({'username': username})


def insert_user(username, hashed_password):
    return mongo.db.users.insert_one({'username': username, 'password': hashed_password})


def insert_film(title, opinion, filename, user_id):
    return mongo.db.films.insert_one({
        'title': title,
        'opinion': opinion,
        'image': filename,
        'user_id': user_id
    })


def find_films_by_user_id(user_id):
    return mongo.db.films.find({'user_id': user_id})


def find_film_by_id(film_id):
    return mongo.db.films.find_one({"_id": ObjectId(film_id)})


def delete_film(film_id):
    return mongo.db.films.delete_one({"_id": ObjectId(film_id)})
