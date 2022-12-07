# Groundup
Welcome to Groundup, a decentralized data collection platform that connects data collectors to data seekers. 

We enable researchers, government, and private companies to obtain high quality, local, timely data from villages in rural India.

![alt text](/static/About.png)

## Video Overview:
[Groundup: CS50 Final Project Demo](https://youtu.be/rZiRzh7lkxU)

## Getting Started:
- Download the Groundup repository folder to your computer
- Use `cd` in terminal to make the Groundup folder your current working directory
- Create a Python virtual environment with `python3 -m venv venv`
- Execute `. venv/bin/activate` to activate the environment
- Ensure that pip is installed by running `pip3 --version`, if not, install pip [these instructions](https://pip.pypa.io/en/stable/installation/)
- Install Flask and other required dependencies with `pip3 install [dependency name]`. 
    - For example: `pip install Flask`
    - See requirements.txt for a list of all the dependencies that need to be installed
- Run `flask run` to start the website
- Check the terminal for an output like: "Running on http://127.0.0.1:5000"
- Navigate to this link in your browser
- Groundup is now running locally

## Using Groundup:
- Navigate to register in the navbar to register as a data collector or client
- Login to the data collector or client dashboards
    - You can log in with the credentials you registerd with, or with these existing credentials which already have associated data:
    - Client:
        - Username: "groundupcli"
        - Password: "groundupcli"
    - Data collectors:
        - Username1: "coll1"
        - Password1: "coll1"
        - Username2: "coll2"
        - Password2: "coll2"
        - Username3: "coll3"
        - Password3: "coll3"
- When logged in as a data collector, you can view or create/edit your profile in the dashboard. This allows clients to see your profile on an interactive map.
- When logged in as a client, you can match with data collectors using the filter in the dashboard. If you want to see all of the registered data collectors, simply press "match" without inputting any filters. Data collectors are visualized on an interactive map.

## Authors:
**Alex Wong**: [AlexW1001](https://github.com/AlexW1001) and **Mohan Hathi**: [MohanMaker](https://github.com/MohanMaker)

This was created as a final project for Harvard's Fall 2022 session of [CS50](https://cs50.harvard.edu/college/2022/fall/).