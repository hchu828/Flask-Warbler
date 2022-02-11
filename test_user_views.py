"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Likes.query.delete()

        self.client = app.test_client()

        u = User(
        email="test@test.com",
        username="testuser",
        password="HASHED_PASSWORD"
        )

        u2 = User(
        email="test2@test.com",
        username="testuser2",
        password="HASHED_PASSWORD"
        )

        db.session.add_all([u, u2])
        db.session.commit()

        self.u_id = u.id
        self.u2_id = u2.id


    def test_get_users(self):
        """Can we see list of users"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u.id

            resp = c.get('/users')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("<!--Flask Testing Comment 'index.html'-->", html)

    def test_get_user_by_id(self):
        """Can we see list of users"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u.id

            resp = c.get(f'/users/{self.u.id}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("<!--Flask Testing Comment 'show.html'-->", html)

    def test_follow_user(self):
        """Can we follow a user"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u.id

            breakpoint()

            resp = c.post(f'/users/follow/{self.u2.id}')
            
            self.assertEqual(resp.status_code, 302)
            self.assertIn(self.u2, self.u.following)