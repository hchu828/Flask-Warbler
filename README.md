# Flask-Warbler

#Set up Python virtual environemnt:
$ python3 -m venv venv
$ source venv/bin/activate
(venv) $ pip install -r requirements.txt

#Set up the database:
(venv) $ psql
=# CREATE DATABASE warbler;
=# (control-d)
(venv) $ python seed.py

#Create an .env folder:
SECRET_KEY=abc123
DATABASE_URL=postgresql:///warbler

#Start server:
(venv) $ flask run
