from flask import Flask, render_template, request, redirect, url_for
from pycognito import Cognito
import pymongo
from settings import Config

app = Flask(__name__)

# DocumentDB
# CLUSTER_ENDPOINT = 'docdb-2021-06-05-13-32-53.cluster-cj6vdcmjcqfb.ap-southeast-1.docdb.amazonaws.com'
# DB_USERNAME = 'forumsbook'
# DB_PASSWORD = 'dNhBnvXBBE99u5'

aws_cognito = Cognito(Config.USER_POOL_ID, Config.CLIENT_ID, username=Config.USER_POOL_NAME)
# mongo_client = pymongo.MongoClient(CLUSTER_ENDPOINT, username=DB_USERNAME, password=DB_PASSWORD, retryWrites='false')

loggedIn_user = None


@app.route("/")
def root():
    # try:
    #     db = mongo_client.forumsbook
    #     col = db.users
    #     col.insert_one({'hello': 'Amazon DocumentDB'})
    # except Exception as e:
    #     print('Error')
    #     print(e)

    if loggedIn_user is not None:
        return render_template("forum.html")

    return render_template("home.html")


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            global loggedIn_user
            loggedIn_user = Cognito(Config.USER_POOL_ID, Config.CLIENT_ID, username=Config.USER_POOL_NAME)
            loggedIn_user.authenticate(password)
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
            return redirect(url_for('root'))
        except Exception as e:
            return render_template('register.html', error_msg=e)

    else:
        return render_template('register.html')


@app.route('/email-verification', methods=["POST"])
def emailVerification():
    if request.method == "POST":
        user_name = request.form.get("user_name")
        ver_code = request.form.get("ver_code")

        try:
            aws_cognito.confirm_sign_up(ver_code, user_name)
            return redirect(url_for('root'))
        except Exception as e:
            return render_template('email-verification.html', error_msg=e)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
