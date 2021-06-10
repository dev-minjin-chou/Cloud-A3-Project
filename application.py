import datetime

import boto3
import pymongo
import requests
from boto3.dynamodb.conditions import Key
from bson.objectid import ObjectId
from flask import Flask, render_template, request, redirect, url_for, flash
from pycognito import Cognito

from mail import MailSender
from settings import Config
import jwt

application = app = Flask(__name__)

aws_cognito = Cognito(Config.USER_POOL_ID, Config.CLIENT_ID, username=Config.USER_POOL_NAME)
mongo_client = pymongo.MongoClient(Config.DB_HOST, username=Config.DB_USERNAME,
                                   password=Config.DB_PASSWORD, retryWrites='false')

loggedIn_user = None
loggedIn_username = None
DATE_TIME_FORMAT = "%Y-%m-%d, %H:%M:%S"
DB_POST_COLLECTION = 'posts'


@app.route("/")
def root():
    if loggedIn_username is None:
        return render_template("home.html")

    db = mongo_client.get_database(Config.DB_NAME)
    db_posts = list(db.get_collection(DB_POST_COLLECTION).find())

    posts = []
    for post in db_posts:
        posts.append(
            {'_id': post['_id'], 'message': post['message'], 'postedAt': post['postedAt'].strftime(DATE_TIME_FORMAT),
             'postedBy': post['postedBy']})

    return render_template("forum.html", posts=posts, username=loggedIn_username)


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            global loggedIn_user
            loggedIn_user = Cognito(Config.USER_POOL_ID, Config.CLIENT_ID, username=username)
            loggedIn_user.authenticate(password)

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
            cognito_response = aws_cognito.register(username, password)
            app.logger.debug('Cognito response:')
            app.logger.debug(cognito_response)
        except Exception as e:
            app.logger.error('AWS Cognito API error')
            app.logger.error(e)
            return render_template('register.html', error_msg=e)

        return render_template('email-verification.html', email=user_email, username=username)
    else:
        return render_template('register.html')


@app.route('/logout', methods=["GET"])
def logout():
    global loggedIn_user
    user = vars(loggedIn_user)
    id_token = user['id_token']
    refresh_token = user['refresh_token']
    access_token = user['access_token']
    cognito = Cognito(Config.USER_POOL_ID, Config.CLIENT_ID,
                      id_token=id_token, refresh_token=refresh_token,
                      access_token=access_token)
    cognito.logout()
    global loggedIn_username
    loggedIn_username = None

    return redirect(url_for('root'))


@app.route('/create-post', methods=["POST"])
def createPost():
    message = request.form.get("message")

    try:
        payload = {'message': message, "username": loggedIn_username, 'timestamp': datetime.datetime.now().isoformat()}
        app.logger.debug('Sending create post api request with payload')
        app.logger.debug(payload)
        requests.post(Config.CREATE_POST_API, json=payload)
    except Exception as e:
        app.logger.error('Sending create post api error')
        app.logger.error(e)
        return render_template('forum.html', error_msg=e)

    return redirect(url_for('root'))


@app.route('/users/<string:username>/posts/<string:post_id>', methods=["GET"])
def viewPost(username, post_id):
    if request.method == "POST":
        return redirect(url_for('root'))

    try:
        db = mongo_client.get_database(Config.DB_NAME)
        post = db.get_collection(DB_POST_COLLECTION).find_one({'_id': ObjectId(post_id)})
        post['postedBy'] = username
        return render_template('post.html', post=post)
    except Exception as e:
        return render_template('post.html', error_msg=e)


@app.route('/post', methods=["POST"])
def likePost():
    try:
        if loggedIn_user is None:
            flash('Missing user credential, please login again', 'error')
            return redirect(url_for('root'))

        access_token = loggedIn_user.id_token
        app.logger.debug(f'Decoding token {access_token}')
        decoded = jwt.decode(access_token, algorithms=["RS256"], options={"verify_signature": False})
        email = decoded['email']
        app.logger.debug(f'Got email {email}')
    except Exception as e:
        app.logger.error('Decoding error')
        app.logger.error(e)

        flash(str(e), 'danger')
        return redirect(url_for('root'))

    try:
        posted_by = request.form.get("postedBy")
        mailSender = MailSender(Config.SENDER_EMAIL)

        mail_subject = f'{posted_by} just liked your post'
        app.logger.debug(f'Sending mail with subject {mail_subject}')

        mailSender.sendMail(mail_subject, email)
    except Exception as e:
        app.logger.error('Sending email error')
        app.logger.error(e)
        flash(str(e), 'danger')

    return redirect(url_for('root'))


@app.route('/email-verification', methods=["POST"])
def verifyEmail():
    if request.method == "POST":
        username = request.form.get("username")
        ver_code = request.form.get("ver_code")

        try:
            aws_cognito.confirm_sign_up(ver_code, username)

            global loggedIn_username
            loggedIn_username = username
        except Exception as e:
            app.logger.error('Email verification error')
            app.logger.error(e)
            return render_template('email-verification.html', error_msg=e)

        flash('You have successfully registered.', 'success')
        return redirect(url_for('root'))


@app.route('/change-password', methods=["POST", "GET"])
def changePassword():
    if request.method == "POST":
        prev_password = request.form.get("prev_password")
        new_password = request.form.get("new_password")

        try:
            global loggedIn_user
            if loggedIn_user is None:
                return render_template('login.html', error_msg='User not logged in')

            loggedIn_user.change_password(prev_password, new_password)

            # todo: get phone number of this user and send sms message
            # sns = boto3.client('sns')
            # number = '+17702233322'
            # sns.publish(PhoneNumber=number,
            #             Message='Did you change your password? If not, please secure your account by resetting '
            #                     'password.')

            flash('Your password has been reset successfully', 'success')
            return redirect(url_for('root'))
        except Exception as e:
            error_msg = e
            return render_template('change-password.html', error_msg=error_msg)
    return render_template("change-password.html")


if __name__ == '__main__':
    if Config.DEVELOPMENT == 'true':
        app.debug = True

    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'

    app.run(host='127.0.0.1', port=8080)
