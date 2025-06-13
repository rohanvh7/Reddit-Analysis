# Dagster Reddit ETL Project

This project uses [Dagster](https://dagster.io/) to create a simple ETL (Extract, Transform, Load) pipeline that fetches new submissions from a specified subreddit using the Reddit API and stores them in a local SQLite database.

## Overview

The pipeline consists of a single Dagster asset, `reddit_submissions`, which is responsible for:
1.  **Extracting** data from a subreddit using the PRAW (Python Reddit API Wrapper) library.
2.  **Transforming** the data by checking for duplicates against the existing records in the database.
3.  **Loading** only the new submissions into a SQLite `submissions` table.

The project is designed to be configurable, allowing you to easily change the target subreddit and the number of posts to fetch.

---

## Prerequisites

* Python 3.8+
* A Reddit account with API credentials.
* [uv](https://github.com/astral-sh/uv) (a fast Python package installer and resolver).
* `praw>=7.8.1`

---

## Setup and Installation

1.  **Clone the Repository (Optional)**
    If this project were in a Git repository, you would start by cloning it:
    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```

2.  **Create a Virtual Environment**
    It's highly recommended to use a virtual environment. `uv` can create one for you.
    ```bash
    uv venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    ```

3.  **Configure `pyproject.toml`**
    Create a `pyproject.toml` file in the root of your project with the following content. This file defines the project's dependencies.

    ```toml
    [project]
    name = "dagster-reddit-etl"
    version = "0.1.0"
    requires-python = ">=3.8"
    dependencies = [
        "dagster",
        "dagit",
        "praw>=7.8.1",
        "python-dotenv",
    ]
    ```

4.  **Install Dependencies with `uv`**
    With your virtual environment activated, use `uv sync` to install all the dependencies defined in `pyproject.toml`.
    ```bash
    uv sync
    ```

5.  **Configure Environment Variables**
    This project uses a `.env` file to securely manage your Reddit API credentials. Create a file named `.env` in the root directory of the project.

    Copy the following format into your `.env` file and replace the placeholder values with your actual Reddit credentials.

    ```ini
    # .env file
    REDDIT_CLIENT_ID="YOUR_CLIENT_ID_HERE"
    REDDIT_CLIENT_SECRET="YOUR_CLIENT_SECRET_HERE"
    REDDIT_USERNAME="YOUR_USERNAME_HERE"
    REDDIT_PASSWORD="YOUR_PASSWORD_HERE"
    REDDIT_USER_AGENT="MyDagsterApp/0.1 by u/YourUsername"
    ```
    > **Important**: Add `.env` to your `.gitignore` file to prevent your secrets from being committed to version control.

---

## How to Run the Project

With your virtual environment activated and your `.env` file configured, you can launch the Dagster UI.

1.  **Add `dagster` to `uv`'s toolchain (Optional but Recommended)**
    This allows you to run `dagster` commands directly.
    ```bash
    uv tool install dagster
    ```

2.  **Start the Dagster UI**
    From your project's root directory (the one containing `definitions.py`), run the following command:
    ```bash
    dagster dev
    ```

3.  **Access the UI**
    Open your web browser and navigate to [http://localhost:3000](http://localhost:3000).

4.  **Materialize the Asset**
    In the Dagster UI, you will see the `reddit_submissions` asset. To run the pipeline:
    * Click on the `reddit_submissions` asset in the asset graph.
    * Click the **"Materialize"** button in the top right corner.

    Dagster will execute the asset, and you will see the logs in the run viewer. Upon successful completion, a `submissions.db` file will be created in your project directory containing the fetched posts.

---

## Credits
* **AI Assistance**: [Gemini 2.5 Pro](https://deepmind.google/technologies/gemini/)
* **Reddit API Wrapper**: [Praw](https://praw.readthedocs.io)

