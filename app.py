from http.client import UNAUTHORIZED
import os

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
from werkzeug.exceptions import Unauthorized
from sqlalchemy import or_

from forms import CSRFProtectForm, EditUserForm, UserAddForm, LoginForm, MessageForm
from models import db, connect_db, User, Message, Likes, DEFAULT_PROFILE_IMAGE, DEFAULT_HEADER_IMAGE

load_dotenv()

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.getenv('DATABASE_URL'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

debug = DebugToolbarExtension(app)


connect_db(app)


##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


@app.before_request
def add_csrf_token_to_g():
    """Add CSRF token to Flask global"""

    g.form = CSRFProtectForm()


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    g.form = UserAddForm()

    if g.form.validate_on_submit():
        try:
            user = User.signup(
                username=g.form.username.data,
                password=g.form.password.data,
                email=g.form.email.data,
                image_url=g.form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html')

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    g.form = LoginForm()

    if g.form.validate_on_submit():
        user = User.authenticate(g.form.username.data,
                                 g.form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html')


@app.post('/logout')
def logout():
    """Handle logout of user."""

    if g.form.validate_on_submit():
        do_logout()
        flash("Logout Success!")
        return redirect("/")

    else:
        flash("Invalid credentials.", 'danger')
        raise Unauthorized()


##############################################################################
# General user routes:

@app.get('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.get('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)

    liked_messages_count = Likes.query.filter(Likes.user_id == user_id).count()

    session['LAST_URL'] = f'/users/{user_id}'

    return render_template('users/show.html',
                           user=user,
                           liked_messages_count=liked_messages_count)


@app.get('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)

    liked_messages_count = Likes.query.filter(Likes.user_id == user_id).count()

    return render_template('users/following.html', user=user, liked_messages_count=liked_messages_count)


@app.get('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)

    liked_messages_count = Likes.query.filter(Likes.user_id == user_id).count()

    return render_template('users/followers.html', user=user, liked_messages_count=liked_messages_count)


@app.get('/users/<int:user_id>/liked_messages')
def show_users_liked_messages(user_id):
    """Shows a list of all messsages the user has liked"""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)

    liked_messages_count = Likes.query.filter(Likes.user_id == user_id).count()
    #CODE REVIEW len(user.likes)

    session['LAST_URL'] = f'/users/{user_id}/liked_messages'

    return render_template('users/likes.html', user=user, liked_messages_count=liked_messages_count)


@app.post('/users/follow/<int:follow_id>')
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized. NO USER", "danger")
        return redirect("/")

    if g.form.validate_on_submit():
        followed_user = User.query.get_or_404(follow_id)
        g.user.following.append(followed_user)
        db.session.commit()

        return redirect(f"/users/{g.user.id}/following")

    flash("Access unauthorized. NOT VALIDATING FORM", "danger")
    return redirect("/")


@app.post('/users/stop-following/<int:follow_id>')
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    if g.form.validate_on_submit():
        followed_user = User.query.get(follow_id)
        g.user.following.remove(followed_user)
        db.session.commit()

        return redirect(f"/users/{g.user.id}/following")

    flash("Access unauthorized.", "danger")
    return redirect("/")


@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    g.form = EditUserForm(obj=g.user)

    if g.form.validate_on_submit():
        if User.authenticate(g.user.username, g.form.password.data):
            g.user.username = g.form.username.data
            g.user.email = g.form.email.data
            g.user.image_url = g.form.image_url.data or DEFAULT_PROFILE_IMAGE
            g.user.header_image_url = g.form.header_image_url.data or DEFAULT_HEADER_IMAGE
            g.user.bio = g.form.bio.data

            db.session.commit()
            return redirect(f'/users/{g.user.id}')
        else:
            bad_form = EditUserForm(
                username=g.form.username.data,
                email=g.form.email.data,
                image_url=g.form.image_url.data,
                header_image_url=g.form.header_image_url,
                bio=g.form.bio.data
            )

            g.form = bad_form
            flash('Incorrect Password', 'danger')
            return render_template('/users/edit.html')

    else:
        return render_template('/users/edit.html')


@app.post('/users/delete')
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    if g.form.validate_on_submit():
        do_logout()

        db.session.delete(g.user)
        db.session.commit()

        return redirect("/signup")

    else:
        flash("Access unauthorized.", "danger")
        return redirect("/")


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    g.form = MessageForm()

    if g.form.validate_on_submit():
        msg = Message(text=g.form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/new.html')


@app.get('/messages/<int:message_id>')
def messages_show(message_id):
    """Show a message."""

    msg = Message.query.get(message_id)
    return render_template('messages/show.html', message=msg)


@app.post('/messages/<int:message_id>/delete')
def messages_destroy(message_id):
    """Delete a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    if g.form.validate_on_submit():
        msg = Message.query.get(message_id)
        db.session.delete(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    flash("Access unauthorized.", "danger")
    return redirect("/")

##############################################################################
# Homepage and error pages


@app.get('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """

    if g.user:
        following_ids = [user.id for user in g.user.following]

        messages = (Message
                    .query
                    .filter(or_(Message.user_id.in_(following_ids),
                                Message.user_id == g.user.id))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

        session['LAST_URL'] = '/'

        return render_template('home.html', messages=messages)

    else:
        return render_template('home-anon.html')


##############################################################################
# Routes for Like and Unliking

#CODE REVIEW - name - togglelikes
#Experiemnt with moving some of the mathy logic to the model(s)
@app.post('/messages/<int:message_id>/togglelike')
def like_message(message_id):
    """Likes or unlikes the message a user clicks
    Creates database entry
    Return render_template of the same page with star liked
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    if g.form.validate_on_submit():
        liked_message = Likes.query.filter(
                        Likes.message_id == message_id and 
                        Likes.user_id == g.user.id).one_or_none()

        if g.user.is_author(message_id):
            flash("You cannot like your own messages..", "danger")
            return redirect("/")

        if not liked_message:
            like = Likes(message_id=message_id, user_id=g.user.id)
            db.session.add(like)

        else:
            db.session.delete(liked_message)

        db.session.commit()

        return redirect(session['LAST_URL'])


##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(response):
    """Add non-caching headers on every request."""

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
    response.cache_control.no_store = True
    return response
