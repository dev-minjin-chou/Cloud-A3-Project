const AWS = require("aws-sdk");
const dynamodb = new AWS.DynamoDB({
    region: "us-east-1",
    apiVersion: "2012-08-10"
});

exports.handler = (event, context, callback) => {

    var body = JSON.parse(event.body);
    const params = {
        Item: {
            email : {
                S: body.email
            },
            user_name : {
                S: body.user_name
            },
            password : {
                S: body.password
            }
        },
        TableName: "forum-login"
    };
    console.log(params);
    dynamodb.putItem(params, (err, data) => {
        if (err) {
            console.log(err);
            callback(err);
        } else {
            const response = {
                statusCode: 200,
                headers: {
                    "Access-Control-Allow-Headers" : "Content-Type",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
            },
            body: JSON.stringify({ 
              email: params.Item.email.S,
              user_name: params.Item.user_name.S,
              password: params.Item.password.S
            }),
        };
          callback(null, response);
        }

    });
};