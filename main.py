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


@app.route('/signup', methods=["POST", "GET"])
def signup():

    if request.method == "POST":
        return render_template('login.html', error_msg=error_msg)
    else:
        return render_template('signup.html')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)

