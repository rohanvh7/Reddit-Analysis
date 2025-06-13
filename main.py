from praw import Reddit
from db.models import Submission
from db import database_service
from db.models import Base
from sqlalchemy import select
from datetime import datetime,timezone
import configparser
from sqlite3 import IntegrityError

import logging

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

for logger_name in ("praw", "prawcore"):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
def reddit_instance() -> Reddit:
    config = configparser.ConfigParser()
    config.read('.env')
    config.sections()
    client_id=config['CREDS']['client_id']
    client_secret=config['CREDS']['client_secret']
    password=config['CREDS']['password']
    user_agent=config['CREDS']['user_agenta']
    username=config['CREDS']['username']

    #remember avoid double quotes around creds and secrets

    reddit = Reddit(client_id=client_id,
                    client_secret=client_secret,
                    password=password,
                    user_agent=user_agent, #<platform>:<app ID>:<version string> 
                    username=username)
    return reddit

if __name__ == "__main__":

    config = configparser.ConfigParser()
    config.read('config.ini')
    config

    maintainance_mode=config['ENVIRONMENT']['MAINTAINANCE']
    subreddit_name=config['SUBMISSION']['SUBREDDIT']
    posts_fetch_limit=config['SUBMISSION']['LIMIT']

    path=config['DATABASE']['FILE_PATH']

    reddit = reddit_instance()

    if str(maintainance_mode) == 'True':
        print(reddit.user.me())
    else:
        session=database_service.Session(db_path=path)    
        posts=[]

        
        for submission in reddit.subreddit(subreddit_name).new(limit=posts_fetch_limit):
            submission_id=submission.id
            submission_title=submission.title
            submission_url=submission.url
            submission_time=datetime.fromtimestamp(submission.created_utc,timezone.utc)
            submission_text=submission.selftext
            post=Submission(submission_id=submission_id,submission_title=submission_title,submission_url=submission_url,submission_time=submission_time,submission_text=submission_text)
            posts.append(post)


        with session.get_session() as sqlite_session:
            engine=session.get_engine()
            Base.metadata.create_all(engine)
            try:
                sqlite_session.add_all(posts)
            except IntegrityError:
                sqlite_session.rollback()

            sqlite_session.commit()
            statement =select(Submission)
            posts_obj = sqlite_session.scalars(statement).all()


