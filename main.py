from flask import Flask, render_template, request, url_for, redirect, send_file
from decimal import Decimal
import logging
import json
import boto3
import requests
import os
import tempfile
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr


app = Flask(__name__)

@app.route("/")
def root():
    return render_template("login.html")


@app.route('/login', methods=["POST", "GET"])
def login():

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        error_msg = None

        try: 
            query_result1 = query(email)
            if len(query_result1) > 0:
                if email != query_result1[0]['email']:
                    error_msg = 'Email or password is invalid'
                    return render_template('login.html', error_msg=error_msg)
                elif password != query_result1[0]['password']:
                    error_msg = 'Email or password is invalid'
                    return render_template('login.html', error_msg=error_msg)
                else:
                    global username_login, email_login
                    email_login = query_result1[0]['email']
                    username_login = query_result1[0]['user_name']
                    subscriptions = get_musics(username_login)
                    return render_template('main.html', error_msg=error_msg, username_login=username_login, subscriptions=subscriptions)
            else:
                error_msg = 'Email or password is invalid'
                return render_template('login.html', error_msg=error_msg)

        except Exception as e:
            error_msg = e
        return render_template('login.html', error_msg=error_msg)
    else:
        return render_template('login.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

