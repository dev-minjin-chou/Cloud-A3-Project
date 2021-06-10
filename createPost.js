const AWS = require("aws-sdk");
const dynamodb = new AWS.DynamoDB({
    region: "us-east-1",
    apiVersion: "2012-08-10"
});

exports.handler = (event, context, callback) => {
    const body = JSON.parse(event.body);
    const {message, username, timestamp} = body
    const params = {
        Item: {
            message: {
                S: message
            },
            username: {
                S: username
            },
            timestamp: {
                S: timestamp
            }
        },
        TableName: "forum-post"
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
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
                },
                body: JSON.stringify({
                    message,
                    username,
                    timestamp
                }),
            };
            // callback response
            callback(null, response);
        }

    });
};