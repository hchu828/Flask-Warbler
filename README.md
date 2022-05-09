# Flask-Warbler

#The Flask-Warbler server-side application is a mock of a popular blog site. It has built-in authentication patterns so that users can register and login with an account and post messages, like messages, and follow other users. 

<img width="1427" alt="Warbler_homepage" src="https://user-images.githubusercontent.com/40369796/167470648-810141d6-1726-40d2-840c-aaf1366f5f0a.png">

<img width="1408" alt="Warbler_account" src="https://user-images.githubusercontent.com/40369796/167470613-e6067542-5b02-4520-ae6c-ea86944b7696.png">

###Setup
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



