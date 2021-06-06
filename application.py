import datetime
import uuid

import pymongo
from flask import Flask, render_template, request, redirect, url_for
from pycognito import Cognito

from settings import Config

application = app = Flask(__name__)

aws_cognito = Cognito(Config.USER_POOL_ID, Config.CLIENT_ID, username=Config.USER_POOL_NAME)
mongo_client = pymongo.MongoClient(Config.DB_HOST, username=Config.DB_USERNAME,
                                   password=Config.DB_PASSWORD, retryWrites='false')

loggedIn_user = None
DATE_TIME_FORMAT = "%Y-%m-%d, %H:%M:%S"


@app.route("/")
def root():
    if loggedIn_user is None:
        return render_template("home.html")

    db = mongo_client.get_database(Config.DB_NAME)
    users = db.get_collection('users').find()
    posts = []
    for u in users:
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

            global loggedIn_user
            loggedIn_user = username

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
            return render_template('email-verification.html', email=user_email)
        except Exception as e:
            return render_template('register.html', error_msg=e)

    else:
        return render_template('register.html')


@app.route('/create-post', methods=["POST"])
def createPost():
    subject = request.form.get("subject")
    message = request.form.get("message")

    try:
        db = mongo_client.get_database(Config.DB_NAME)
        users = db.get_collection('users')
        user = users.find_one({'username': loggedIn_user})
        post = {'id': str(uuid.uuid4()), 'subject': subject, 'message': message, 'postedAt': datetime.datetime.now()}

        if user is None:
            users.insert_one({'username': loggedIn_user, 'posts': [post]})
        else:
            update_document = {
                '$push': {"posts": post}
            }
            users.update_one({'username': loggedIn_user}, update_document)

        return redirect(url_for('root'))
    except Exception as e:
        return render_template('forum.html', error_msg=e)


@app.route('/posts/<string:post_id>', methods=["GET"])
def viewPost(post_id):
    if request.method == "POST":
        return redirect(url_for('root'))

    try:
        db = mongo_client.get_database(Config.DB_NAME)
        results = db.get_collection('users').find_one({'username': loggedIn_user},
                                                    {'posts': {
                                                        "$elemMatch": {
                                                            "id": post_id
                                                        }
                                                    }})
        post = results['posts'][0]
        post['postedBy'] = loggedIn_user
        return render_template('post.html', post=post)
    except Exception as e:
        return render_template('post.html', error_msg=e)


@app.route('/post', methods=["POST"])
def likePost():
    return redirect(url_for('root'))


@app.route('/email-verification', methods=["POST"])
def emailVerification():
    if request.method == "POST":
        username = request.form.get("username")
        ver_code = request.form.get("ver_code")

        try:
            aws_cognito.confirm_sign_up(ver_code, username)

            global loggedIn_user
            loggedIn_user = username

            return redirect(url_for('root'))
        except Exception as e:
            return render_template('email-verification.html', error_msg=e)


if __name__ == '__main__':
    if Config.DEVELOPMENT == 'true':
        app.debug = True
    app.run(host='127.0.0.1', port=8080)
