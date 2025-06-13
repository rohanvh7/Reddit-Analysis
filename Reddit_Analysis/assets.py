import sqlite3
from configparser import ConfigParser

import praw
import pandas as pd

from dagster import (
    asset,
    Config,
    AssetExecutionContext,
    ConfigurableResource,
    ResourceParam,
    MaterializeResult,
    MetadataValue
)

# --- Resources ---

class PrawResource(ConfigurableResource):
    """A Dagster resource for interacting with the Reddit API using PRAW."""

    client_id: str
    client_secret: str
    username: str
    password: str
    user_agent: str

    def get_client(self):
        """Initializes and returns a PRAW Reddit instance."""
        return praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            username=self.username,
            password=self.password,
            user_agent=self.user_agent,
        )

class SQLiteResource(ConfigurableResource):
    """
    A Dagster resource for connecting to a SQLite database.
    It acts as a context manager to handle connection opening/closing.
    """

    database_path: str

    def _initialize_db(self, conn):
        """Creates the submissions table if it doesn't exist."""
        with conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id TEXT PRIMARY KEY,
                title TEXT,
                score INTEGER,
                url TEXT,
                num_comments INTEGER,
                created_utc REAL,
                author TEXT,
                post_data TEXT
            )
            """)

    def get_connection(self):
        """Returns a SQLite connection."""
        conn = sqlite3.connect(self.database_path)
        # Initialize the database schema on first connection
        self._initialize_db(conn)
        return conn

# --- Asset Configuration ---

# --- Asset Configuration ---

class AppConfigLoader:
    """A dedicated class to load configuration from the config.ini file."""
    def __init__(self, config_file='config.ini'):
        self.parser = ConfigParser()
        self.parser.read(config_file)

    def get_subreddit(self, fallback='RelationShipIndia'):
        """Gets the subreddit from the 'reddit' section of the config."""
        return self.parser.get('reddit', 'subreddit', fallback=fallback)

    def get_limit(self, fallback=100):
        """Gets the submission limit from the 'reddit' section of the config."""
        return self.parser.getint('reddit', 'limit', fallback=fallback)

# Instantiate the loader
config_loader = AppConfigLoader()

class RedditConfig(Config):
    """
    Configuration for the reddit_submissions asset.
    Defaults are now loaded via the AppConfigLoader class.
    """
    subreddit: str = config_loader.get_subreddit()
    limit: int = config_loader.get_limit()

# --- Asset Definition ---

@asset(
    description="Fetches new posts from a subreddit and stores them in a SQLite database."
)
def reddit_submissions(
    context: AssetExecutionContext,
    config: RedditConfig,
    praw_resource: ResourceParam[PrawResource],
    sqlite_resource: ResourceParam[SQLiteResource],
) -> None:
    """
    Fetches new posts from a specified subreddit and appends them to a SQLite database,
    ensuring that duplicate submissions are not added.
    """
    reddit_client = praw_resource.get_client()
    context.log.info(f"Successully initialized Reddit client")

    context.log.info(f"Preparing client to fetch posts from r/{config.subreddit}")
    subreddit = reddit_client.subreddit(config.subreddit)

    # First, fetch all the data you need from the external API
    context.log.info(f"Fetching latest {config.limit} posts from r/{config.subreddit}")
    fetched_posts = []
    for submission in subreddit.new(limit=config.limit):
        fetched_posts.append({
            "id": submission.id,
            "title": submission.title,
            "score": submission.score,
            "url": submission.url,
            "num_comments": submission.num_comments,
            "created_utc":submission.created_utc,
            "author": str(submission.author),
            "post_data":str(submission.selftext)
        })

    # Now, open the database connection and perform all DB operations
    with sqlite_resource.get_connection() as conn:
        cursor = conn.cursor()

        # 1. Read existing IDs
        cursor.execute("SELECT id FROM submissions")
        existing_ids = {row[0] for row in cursor.fetchall()}
        context.log.info(f"Found {len(existing_ids)} existing submissions in the database.")

        # 2. Filter for new posts
        new_posts = [post for post in fetched_posts if post["id"] not in existing_ids]

        if not new_posts:
            context.log.info("No new posts found to add to the database.")
            # The 'with' block will automatically close the connection upon exiting
            return

        context.log.info(f"Found {len(new_posts)} new posts to add.")

        # 3. Write new posts
        insert_query = """
            INSERT INTO submissions (id, title, score, url, num_comments, created_utc, author,post_data)
            VALUES (:id, :title, :score, :url, :num_comments, :created_utc, :author,:post_data)
        """
        cursor.executemany(insert_query, new_posts)
        conn.commit()
        context.log.info(f"Successfully appended {len(new_posts)} new submissions to the database.")
    # The connection is now safely closed here


@asset(
    description="Previews the 10 most recent submissions from the database.",
    deps=[reddit_submissions] # This establishes the dependency
)
def preview_top_submissions(context: AssetExecutionContext, sqlite_resource: ResourceParam[SQLiteResource]) -> MaterializeResult:
    """
    Queries the SQLite database for the 10 most recent posts and logs them as a table.
    """
    context.log.info("Querying database for top 10 recent submissions.")
    with sqlite_resource.get_connection() as conn:
        # Updated query to calculate the local time on the fly
        query = """
        SELECT
            id,
            title,
            score,
            author,
            datetime(created_utc, 'unixepoch', 'localtime') AS created_local
        FROM
            submissions
        ORDER BY
            created_utc DESC
        LIMIT 10;
        """
        
        # Use pandas to read the SQL query into a DataFrame
        df = pd.read_sql_query(query, conn)

        if df.empty:
            context.log.info("No submissions found in the database.")
            
        # Log the DataFrame as a string, which Dagster will display nicely

    return MaterializeResult(
             metadata={
                "preview": MetadataValue.md(df.to_markdown(index=False)),
            }
        )