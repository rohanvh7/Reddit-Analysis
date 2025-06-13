from setuptools import find_packages, setup

setup(
    name="Reddit_Analysis",
    packages=find_packages(exclude=["Reddit_Analysis_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud",
        "praw"
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
