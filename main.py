import boto3
from boto3.dynamodb.conditions import Key
from flask import Flask, render_template, request
from pycognito import Cognito

app = Flask(__name__)

aws_cognito = Cognito('ap-southeast-1_VXmFIo9H3', '2rmru8n4jfrn7hri8rco7ll0nf', username='User')


# Querying dynamo by email.
def query_dynamo(email, dynamodb=None):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('forum-login')

    response = table.query(
        KeyConditionExpression=Key('email').eq(email),
    )
    return response['Items']


# For creating new user
def create_user(email, username, password, dynamodb=None):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('forum-login')
    response = table.put_item(
        Item={
            'email': email,
            'user_name': username,
            'password': password
        }
    )
    return True


@app.route("/")
def root():
    return render_template("home.html")


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        user_email = request.form.get("email")
        password = request.form.get("password")
        error_msg = None

        try:
            result = query_dynamo(user_email)
            if len(result) > 0:
                if user_email != result[0]['email']:
                    error_msg = 'Email is invalid'
                    return render_template('login.html', error_msg=error_msg)
                elif password != result[0]['password']:
                    error_msg = 'Password is invalid'
                    return render_template('login.html', error_msg=error_msg)
                else:
                    return render_template('main.html', error_msg=error_msg)
            else:
                error_msg = 'An error occured, please try again.'
                return render_template('login.html', error_msg=error_msg)

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
            return render_template('email-verification.html', email=user_email, user_name=username)
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
            return render_template('home.html')
        except Exception as e:
            return render_template('email-verification.html', error_msg=e)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
