# Portfolio execution only; Power BI Desktop stays on the host.
FROM python:3.12.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
WORKDIR /app
COPY requirements-dev.lock ./
RUN pip install --no-cache-dir --require-hashes -r requirements-dev.lock
COPY . .
RUN pip install --no-deps --no-build-isolation -e . && useradd --create-home banking && chown -R banking:banking /app
USER banking
CMD ["python", "-m", "orchestration.run_workflow", "--env", "test"]
