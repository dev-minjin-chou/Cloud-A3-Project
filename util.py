import uuid

import requests
from botocore.exceptions import ClientError

from settings import Config

REGION_NAME = "ap-southeast-1"
BUCKET_NAME = 'assignment03bucket'
TEMP_PATH = '/tmp/'

DB_POST_COLLECTION = 'posts'


def download_image(image_url, filename):
    # get image content
    response = requests.get(image_url)
    # open file and write image content
    file = open(filename, "wb")
    file.write(response.content)
    file.close()


class Helper:
    def __init__(self, logger, s3, mongo_client):
        self.logger = logger
        self.s3 = s3
        self.mongo_client = mongo_client

    def upload_file(self, file, object_name=None):
        """Upload a file to an S3 bucket
        :param file_name: File to upload
        :param bucket: Bucket to upload to
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was uploaded, else False
        """
        file_name = str(uuid.uuid4()) + "." + file.filename.split('.')[1]
        file_path = TEMP_PATH + file_name
        file.save(file_path)

        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = file_name

        # Upload the file
        try:
            response = self.s3.upload_file(file_path, BUCKET_NAME, object_name)
            self.logger.debug('S3 response')
            self.logger.debug(response)
            return object_name
        except ClientError as e:
            self.logger.error(e)
            raise e

    def insert_image_url(self, post_id, objectname):
        # Insert into db
        try:
            insert_data = {'id': post_id,
                           'postImage': f'http://s3-{REGION_NAME}.amazonaws.com/{BUCKET_NAME}/{objectname}'}
            db = self.mongo_client.get_database(Config.DB_NAME)
            post_col = db.get_collection(DB_POST_COLLECTION)
            post_col.insert_one(insert_data)
        except Exception as e:
            self.logger.error(e)
            raise e
