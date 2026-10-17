FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements-production.txt ./
RUN pip install --no-cache-dir -r requirements-production.txt
COPY app.py modeling.py kc_house_data_NaN.csv king_county_house_price_project.ipynb ./
COPY assets ./assets
COPY artifacts/notebook_models.joblib artifacts/notebook_manifest.json ./artifacts/
USER 10001
EXPOSE 8050
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-8050} --workers 1 --threads 4 --timeout 120 --access-logfile - --error-logfile - app:server"]
