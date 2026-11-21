FROM python:3.11-slim

WORKDIR /code

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt

COPY apps/api/app /code/app
COPY analytics /code/analytics
COPY agents /code/agents
COPY sandbox /code/sandbox
COPY connectors /code/connectors
COPY security /code/security

ENV PYTHONPATH=/code:$PYTHONPATH

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
