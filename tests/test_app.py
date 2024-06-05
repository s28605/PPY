from flask_testing import TestCase
from app import app, mongo, bcrypt
import mongomock
import unittest
import os


class FilmAppTestCase(TestCase):

    def create_app(self):
        app.config['TESTING'] = True
        app.config['MONGO_URI'] = 'mongodb://localhost:27017/test_film_db'
        app.config['SECRET_KEY'] = 'test_secret_key'
        app.config['UPLOAD_FOLDER'] = 'static/uploads'
        app.config['LOGIN_DISABLED'] = True

        # Use mongomock to mock MongoDB
        self.mongo = mongomock.MongoClient().db
        mongo.db = self.mongo
        return app

    def setUp(self):
        self.client = self.app.test_client()
        self.db = self.mongo

        # Create the uploads directory if it doesn't exist
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        # Create a test user
        password_hash = bcrypt.generate_password_hash('password').decode('utf-8')
        self.user_id = self.db.users.insert_one({'username': 'testuser', 'password': password_hash}).inserted_id

        # Create a test image file
        with open(os.path.join(app.config['UPLOAD_FOLDER'], 'test_image.png'), 'wb') as f:
            f.write(b"test image content")

    def tearDown(self):
        self.db.users.delete_many({})
        self.db.films.delete_many({})
        # Clean up the uploads directory
        for file in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
            if os.path.isfile(file_path):
                os.unlink(file_path)

    def login(self, username, password):
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_register(self):
        response = self.client.post('/register', data=dict(
            username='newuser',
            password='newpassword'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        user = self.db.users.find_one({'username': 'newuser'})
        self.assertIsNotNone(user)

    def test_login(self):
        response = self.login('testuser', 'password')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Film List', response.data)

    def test_add_film(self):
        self.login('testuser', 'password')
        with open('static/uploads/test_image.png', 'rb') as f:
            response = self.client.post('/add_film', data=dict(
                title='Test Film',
                opinion='This is a test opinion.',
                image=f
            ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        film = self.db.films.find_one({'title': 'Test Film'})
        self.assertIsNotNone(film)
        self.assertEqual(film['opinion'], 'This is a test opinion.')

    def test_delete_film(self):
        self.login('testuser', 'password')
        film_id = self.db.films.insert_one({
            'title': 'Test Film',
            'opinion': 'This is a test opinion.',
            'image': 'test_image.png',
            'user_id': str(self.user_id)
        }).inserted_id
        response = self.client.post(f'/delete_film/{film_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        film = self.db.films.find_one({'_id': film_id})
        self.assertIsNone(film)
        # Ensure the file is deleted
        self.assertFalse(os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], 'test_image.png')))


if __name__ == '__main__':
    unittest.main()
