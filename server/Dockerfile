ARG PYTHON_IMAGE=python:3.9-slim
FROM ${PYTHON_IMAGE}

ARG PIP_INDEX_URL=

WORKDIR /app

COPY requirements.txt .
RUN if [ -n "$PIP_INDEX_URL" ]; then \
      pip install --no-cache-dir -i "$PIP_INDEX_URL" -r requirements.txt; \
    else \
      pip install --no-cache-dir -r requirements.txt; \
    fi

COPY app ./app
COPY admin ./admin

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
