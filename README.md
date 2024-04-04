# FastAPI Project
![coverage](https://img.shields.io/badge/coverage-93%25-darkgreen)

## Requirements

* [Python](https://www.python.org/).
* [Docker](https://www.docker.com/).
* [Poetry](https://python-poetry.org/) for Python package and environment management.

___
## Setup Project

* Make virtual environment: 

By default, the dependencies are managed with [Poetry](https://python-poetry.org/), go there and install it.

You can install all the dependencies with:

```console
$ poetry install
```
* Activate virtual environment:

Then you can start a shell session with the new environment with:

```console
$ poetry shell
```

Make sure your editor is using the correct Python virtual environment.

* Create your own `.env` file based on the template `.env.example`

___
## Running Application

* Start the stack with Docker Compose:

```bash
docker compose up -d
```
* Initialize alembic migrations:

```bash
alembic upgrade head
```
* Starting application:

```bash
py main.py
```

___
## Create docker container with the application

* Create Docker container:

```bash
DOCKER_BUILDKIT=1 docker build --rm . -t photoshare:latest
```

* Run Docker container:

```bash
docker run -d --name photoshare --env-file ./.env -p 8000:8000 photoshare:latest
```

___
## Acessing on local
The application will get started in http://127.0.0.1:8000  

Swagger Documentation: http://127.0.0.1:8000/docs

Redoc Documentation: http://127.0.0.1:8000/redoc
___
## Testing

__For run tests__  
```bash
pytest
```

__For run tests with coverage report__  
```bash
pytest --cov=app tests
```