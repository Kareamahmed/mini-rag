# mini-rag

## Requirements

- Python 3.10+

## Install Python Environment 

1. Make sure Python 3.10 or higher is installed.

2. Create a virtual environment:

```bash
$ python -m venv mini-rag-app
```
3. Activate the environment:

On Linux / macOS
```bash
$ source mini-rag-app/bin/activate
```
On Windows (PowerShell)

```bash
$ mini-rag-app\Scripts\activate
```
## Installation

## Install the required packages
```bash
$ pip install -r requirements.txt
```
### Setup the environment variables

```bash
$ cp .env.example .env
```
Set your environment variables in the `.env` file. Like `GEMINI_API_KEY` value.

### Run Alembic Migration

```bash
$ alembic upgrade head
```

## Run Docker Compose Services

```bash
$ cd docker
$ cp .env.example .env
```

- update `.env` with your credentials



```bash
$ cd docker
$ sudo docker compose up -d
```

## Run the FastAPI server
```bash
$ uvicorn main:app --reload --host 0.0.0.0 --port 5000
```