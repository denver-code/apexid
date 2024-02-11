## Installation

```bash
git clone https://github.com/denver-code/apexid
cd apexid
poetry install
```
And you done with installing!

## Setup
1. Setup your Zitadel `instance` and create a `project`, then `backend` app in this project.
2. Create a JWT private key in backend app, then download `*.json` file to project root
3. Rename `sample.env` to `.env`
4. Copy filename of file-key and paste it to `JWT_KEY_FILE` in `.env` file
5. Set it to the `API_PRIVATE_KEY_FILE` variable in `.env` file
6. Fill the rest of the variables in `.env` file

You done with setup so far!
But you more than welcome to setup database and other stuff.

## Start
There is two ways to start this project:
1. Using `uvicorn`:
```bash
uvicorn app.main:app --port 8000 --host 0.0.0.0
```
You can change port and host to whatever you want.
Also you can add `--reload` flag to reload server on code changes (Useful while you writing some code).

2. (Recommended) Using `docker-compose`:


**WIP: Not working yet!**
```bash
docker-compose up -d
```
