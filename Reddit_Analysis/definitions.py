import os
from dotenv import load_dotenv
from dagster import Definitions

# Import your asset and resource definitions from the assets file
from Reddit_Analysis.assets import reddit_submissions,preview_top_submissions, PrawResource, SQLiteResource

# Load environment variables from the .env file in the project root
load_dotenv()

# --- Load and Validate Credentials ---
# Fetch credentials from environment variables
client_id = os.getenv("REDDIT_CLIENT_ID")
client_secret = os.getenv("REDDIT_CLIENT_SECRET")
username = os.getenv("REDDIT_USERNAME")
password = os.getenv("REDDIT_PASSWORD")
user_agent = os.getenv("REDDIT_USER_AGENT", "a-user-agent-v2") # A default is acceptable for the user agent

# Validate that all required credentials are set. If not, raise an informative error.
if not all([client_id, client_secret, username, password]):
    missing_vars = [
        var_name
        for var_name, value in {
            "REDDIT_CLIENT_ID": client_id,
            "REDDIT_CLIENT_SECRET": client_secret,
            "REDDIT_USERNAME": username,
            "REDDIT_PASSWORD": password,
        }.items()
        if not value
    ]
    raise ValueError(
        f"Missing required Reddit credentials. Please set the following environment variables: {', '.join(missing_vars)}"
    )

# --- Define the Project ---
defs = Definitions(
    assets=[reddit_submissions,preview_top_submissions],
    resources={
        # The key "praw_resource" matches the parameter name in the asset function
        "praw_resource": PrawResource(
            # Now we can safely pass the validated, non-None credentials
            client_id=client_id, # type: ignore
            client_secret=client_secret,# type: ignore
            username=username,# type: ignore
            password=password,# type: ignore
            user_agent=user_agent,# type: ignore
        ),
        # The key "sqlite_resource" also matches the parameter name
        "sqlite_resource": SQLiteResource(database_path="submissions.db"),
    },
)
