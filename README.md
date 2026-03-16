# mini-rag

## Requirements

- Python 3.10+

## Install Python Environment 

1. Make sure Python 3.10 or higher is installed.

2. Create a virtual environment:

```bash
$ python -m venv mini-rag
```
3. Activate the environment:

On Linux / macOS
```bash
$ source mini-rag/bin/activate
```
On Windows (PowerShell)

```bash
$ mini-rag\Scripts\activate
```
## Installation

## Install the required packages
```bash
$ pip install -r requirements.txt
```
Setup the environment variables
```bash
$ cp .env.example .env
```
Set your environment variables in the .env file. Like OPENAI_API_KEY value.

## Run the FastAPI server
```bash
$ uvicorn main:app --reload --host 0.0.0.0 --port 5000
```