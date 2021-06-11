const TABLE_NAME = "forum-post";
const AWS = require("aws-sdk");

AWS.config.update({
    region: "us-east-1",
    apiVersion: "2012-08-10",
});

exports.handler = (event, context, callback) => {
    let id = "";
    if (event.queryStringParameters && event.queryStringParameters.id) {
        console.log("Received id: " + event.queryStringParameters.id);
        id = event.queryStringParameters.id;
    }
    const docClient = new AWS.DynamoDB.DocumentClient();
    if (!id) {
        const params = {
            TableName: TABLE_NAME,
        };
        docClient.scan(params, (err, data) => {
            if (err) {
                console.error(
                    "Unable to query. Error:",
                    JSON.stringify(err, null, 2)
                );
                return callback(null, {
                    statusCode: 400,
                    headers: {
                        "Access-Control-Allow-Headers": "Content-Type",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
                    },
                    body: JSON.stringify(err, null, 2),
                });
            } else {
                console.log("Query succeeded.");

                return callback(null, {
                    statusCode: 200,
                    headers: {
                        "Access-Control-Allow-Headers": "Content-Type",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
                    },
                    body: JSON.stringify(data.Items),
                });
            }
        });
    }

    const params = {
        TableName: TABLE_NAME,
        Key: {
            id,
        },
    };

    docClient.get(params, (err, data) => {
        if (err) {
            console.error(
                "Unable to query. Error:",
                JSON.stringify(err, null, 2)
            );
            callback(null, {
                statusCode: 400,
                headers: {
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
                },
                body: JSON.stringify(err, null, 2),
            });
        } else {
            console.log("Query succeeded.");

            callback(null, {
                statusCode: 200,
                headers: {
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
                },
                body: JSON.stringify(data.Item),
            });
        }
    });
};
