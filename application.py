import datetime
import uuid

import pymongo
from flask import Flask, render_template, request, redirect, url_for
from pycognito import Cognito

from settings import Config
from mail import MailSender

application = app = Flask(__name__)

# aws_cognito = Cognito(Config.USER_POOL_ID, Config.CLIENT_ID, username=Config.USER_POOL_NAME)
mongo_client = pymongo.MongoClient(Config.DB_HOST, username=Config.DB_USERNAME,
                                   password=Config.DB_PASSWORD, retryWrites='false')

loggedIn_username = None
DATE_TIME_FORMAT = "%Y-%m-%d, %H:%M:%S"


@app.route("/")
def root():
    if loggedIn_username is None:
        return render_template("home.html")

    db = mongo_client.get_database(Config.DB_NAME)
    users = db.get_collection('users').find()
    posts = []
    for u in users:
        if 'posts' not in u:
            break

        for post in u['posts']:
            posts.append(
                {'post_id': post['id'], 'subject': post['subject'],
                 'postedAt': post['postedAt'].strftime(DATE_TIME_FORMAT),
                 'username': u['username']})
    return render_template("forum.html", posts=posts)


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            cognito = Cognito(Config.USER_POOL_ID, Config.CLIENT_ID, username=username)
            cognito.authenticate(password)

            global loggedIn_username
            loggedIn_username = username

            return redirect(url_for('root'))
        except Exception as e:
            error_msg = e
            return render_template('login.html', error_msg=error_msg)
    else:
        return render_template('login.html')


@app.route('/register', methods=["POST", "GET"])
def register():
    if request.method == "POST":
        user_email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            aws_cognito.set_base_attributes(email=user_email)
            response = aws_cognito.register(username, password)
            print('Register response')
            print(response)
        except Exception as e:
            return render_template('register.html', error_msg=e)

        try:
            db = mongo_client.get_database(Config.DB_NAME)
            db.get_collection('users').insert_one({'username': username, 'email': user_email})
        except Exception as e:
            return render_template('register.html', error_msg=e)

        return render_template('email-verification.html', email=user_email)
    else:
        return render_template('register.html')


@app.route('/create-post', methods=["POST"])
def createPost():
    subject = request.form.get("subject")
    message = request.form.get("message")

    try:
        db = mongo_client.get_database(Config.DB_NAME)
        users = db.get_collection('users')
        user = users.find_one({'username': loggedIn_username})
        post = {'id': str(uuid.uuid4()), 'subject': subject, 'message': message, 'postedAt': datetime.datetime.now()}

        if user is None:
            users.insert_one({'username': loggedIn_username, 'posts': [post]})
        else:
            update_document = {
                '$push': {"posts": post}
            }
            users.update_one({'username': loggedIn_username}, update_document)

        return redirect(url_for('root'))
    except Exception as e:
        return render_template('forum.html', error_msg=e)


@app.route('/users/<string:username>/posts/<string:post_id>', methods=["GET"])
def viewPost(username, post_id):
    if request.method == "POST":
        return redirect(url_for('root'))

    try:
        db = mongo_client.get_database(Config.DB_NAME)
        results = db.get_collection('users').find_one({'username': username},
                                                      {'posts': {
                                                          "$elemMatch": {
                                                              "id": post_id
                                                          }
                                                      }})
        post = results['posts'][0]
        post['postedBy'] = username
        return render_template('post.html', post=post)
    except Exception as e:
        return render_template('post.html', error_msg=e)


@app.route('/post', methods=["POST"])
def likePost():
    try:
        posted_by = request.form.get("postedBy")
        db = mongo_client.get_database(Config.DB_NAME)
        user = db.get_collection('users').find_one({'username': posted_by})

        if 'email' not in user:
            err_msg = 'This user has not been verified with email'
            print(err_msg)
            return render_template('post.html', error_msg=err_msg)

        email = user['email']
        mailSender = MailSender(Config.SENDER_EMAIL)
        # mailSender.sendMail(f'{loggedIn_username} just liked your post', email)
        return redirect(url_for('root'))
    except Exception as e:
        return render_template('post.html', error_msg=e)


@app.route('/email-verification', methods=["POST"])
def verifyEmail():
    if request.method == "POST":
        username = request.form.get("username")
        ver_code = request.form.get("ver_code")

        try:
            aws_cognito.confirm_sign_up(ver_code, username)

            global loggedIn_username
            loggedIn_username = username

            return redirect(url_for('root'))
        except Exception as e:
            return render_template('email-verification.html', error_msg=e)


if __name__ == '__main__':
    if Config.DEVELOPMENT == 'true':
        app.debug = True
    app.run(host='127.0.0.1', port=8080)
