const AWS = require("aws-sdk");
const dynamodb = new AWS.DynamoDB({
    region: "us-east-1",
    apiVersion: "2012-08-10"
});
const TABLE_NAME = "forum-post"

exports.handler = async (event, context, callback) => {
    let id = ''
    if (event.queryStringParameters && event.queryStringParameters.id) {
        console.log("Received id: " + event.queryStringParameters.id);
        id = event.queryStringParameters.id;
    }
    if (!id) {
        callback(null, {
            statusCode: 400,
            headers: {
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
            },
            body: JSON.stringify({"message": "No id specified"}),
        });
    }

    const params = {
        TableName: TABLE_NAME,
        ProjectionExpression: "#postId, username, message, timestamp",
        KeyConditionExpression: "#postId = :id",
        ExpressionAttributeNames: {
            "#postId": "id"
        },
        ExpressionAttributeValues: {
            ":id": id
        }
    };

    dynamodb.query(params, function (err, data) {
        if (err) {
            console.error("Unable to query. Error:", JSON.stringify(err, null, 2));
            callback(null, {
                statusCode: 400,
                headers: {
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
                },
                body: JSON.stringify(err, null, 2),
            })
        } else {
            console.log("Query succeeded.");

            callback(null, {
                statusCode: 200,
                headers: {
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
                },
                body: JSON.stringify({id}),
            },);
        }
    });
};