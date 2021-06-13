import json
import uuid
from datetime import datetime

import boto3
import jwt
import pymongo
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from pycognito import Cognito

from mail import MailSender
from settings import Config
from util import Helper

application = app = Flask(__name__)

aws_cognito = Cognito(Config.USER_POOL_ID, Config.CLIENT_ID, username=Config.USER_POOL_NAME)
mongo_client = pymongo.MongoClient(Config.DB_HOST, username=Config.DB_USERNAME,
                                   password=Config.DB_PASSWORD, retryWrites='false')

# AWS S3
s3 = boto3.client('s3')
helper = Helper(app.logger, s3, mongo_client)

loggedIn_user = None
loggedIn_username = None

DYNAMODB_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
DATE_TIME_FORMAT = "%Y-%m-%d, %H:%M:%S"


@app.route("/")
def root():
    if loggedIn_username is None:
        return render_template("home.html")

    try:
        post_response = json.loads(requests.get(Config.POST_API).content)
        app.logger.debug('Posts = ', post_response)

        posts = []
        for post in post_response:
            posts.append(
                {'_id': post['id'], 'message': post['message'],
                 'postedAt': datetime.strptime(post['timestamp'], DYNAMODB_TIMESTAMP_FORMAT).strftime(DATE_TIME_FORMAT),
                 'postedBy': post['username']})
        return render_template("forum.html", posts=posts, username=loggedIn_username)
    except Exception as e:
        app.logger.error(f'Getting posts error')
        app.logger.error(e)
        flash(f'Getting posts error: {e}', 'danger')
        return render_template('forum.html')


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
    # Clear global variables
    global loggedIn_username
    loggedIn_username = None
    loggedIn_user = None

    return redirect(url_for('root'))


@app.route('/create-post', methods=["POST"])
def createPost():
    message = request.form.get("message")
    file = request.files['file']
    post_id = str(uuid.uuid4())

    try:
        if loggedIn_user is None:
            flash('Missing user credential, please login again', 'danger')
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
        payload = {'id': post_id, 'message': message, "username": loggedIn_username, 'email': email,
                   'timestamp': datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")}
        app.logger.debug('Sending create post api request with payload')
        app.logger.debug(payload)
        requests.post(Config.POST_API, json=payload)
    except Exception as e:
        app.logger.error('Sending create post api error')
        app.logger.error(e)
        return render_template('forum.html', error_msg=e)

    # If file is chosen, upload to S3
    if file.filename != '':
        try:
            object_name = helper.upload_file(file)
            helper.insert_image_db(post_id, object_name)
        except Exception as e:
            app.logger.error('Upload post image error')
            app.logger.error(e)
            return render_template('forum.html', error_msg=e)

    return redirect(url_for('root'))


@app.route('/users/<string:username>/posts/<string:post_id>', methods=["GET"])
def viewPost(username, post_id):
    if request.method == "POST":
        return redirect(url_for('root'))

    try:
        post = json.loads(requests.get(Config.POST_API + '?id=' + post_id).content)
        post['postedBy'] = username
        post['postedAt'] = datetime.strptime(post['timestamp'], DYNAMODB_TIMESTAMP_FORMAT).strftime(DATE_TIME_FORMAT)

        image_url = helper.get_image_url(post_id)
        if image_url != '':
            post['image'] = image_url

        return render_template('post.html', post=post)
    except Exception as e:
        app.logger.error(f'Getting post with id = {post_id} error')
        app.logger.error(e)
        return render_template('forum.html', error_msg=e)


@app.route('/post', methods=["POST"])
def likePost():
    try:
        email = request.form.get("email")
        username = loggedIn_username
        mailSender = MailSender(Config.SENDER_EMAIL)

        mail_subject = f'{username} just liked your post'
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
        except Exception as e:
            app.logger.error('Email verification error')
            app.logger.error(e)
            return render_template('email-verification.html', error_msg=e)

        flash('You have successfully registered. Plase login.', 'success')
        return redirect(url_for('login'))


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
