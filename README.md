# Cloud-A3-Project

## Members
* CHOU, Minjin (s3641315)
* DECHATHAWEEWAT, Chatchapat (s3679216)

## Records
* Github repository : https://github.com/kuntakinte777/Cloud-A3-Project/tree/develop
* Google drive : https://drive.google.com/drive/folders/1OhxzHH7r0OIU03yHgOCFWwRfZoIrRUBt


## Development
### Prerequisites:
-  Python 3
- Docker
### Running Locally
1. Navigate to this project dictory on terminal.
2. Start database Docker container with `docker-compose up -d`
3. Create `.env` file with the followings:
```bash
DEBUG=true

POST_API=https://vku62j9uff.execute-api.us-east-1.amazonaws.com/dev/posts
REGION_NAME=us-east-1

# Cognito
USER_POOL_ID=us-east-1_Gd3Licbad
CLIENT_ID=1jvdcfk3iut0f258vvc8pd8p2l
USER_POOL_NAME=User

# Database
DB_HOST=127.0.0.1
DB_NAME=admin
DB_USERNAME=root
DB_PASSWORD=example

# Email
SENDER_EMAIL=fudjphfbfj@logicstreak.com
```
4. Execute the following commands:
```bash
# Execute this command only once to create Python virtual environment
python3 -m venv env
# Install all dependencies
pip3 install -r requirements.txt
# Use virtual environment
source venv/bin/activate
# Start application
python3 main.py
```

## Project report:
[report.pdf](https://github.com/kuntakinte777/Cloud-A3-Project/files/9186438/report.pdf)
