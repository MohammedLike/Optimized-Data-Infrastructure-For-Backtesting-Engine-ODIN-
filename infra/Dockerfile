FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY packages ./packages
COPY services ./services
COPY benchmarks ./benchmarks
COPY scripts ./scripts
COPY questdb-query-1781940224994.csv ./

RUN pip install --no-cache-dir -e .

EXPOSE 8000
CMD ["uvicorn", "services.odin_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
