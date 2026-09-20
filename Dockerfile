FROM python:3.12-slim
WORKDIR /app
COPY services/compute_router/app.py /app/app.py
ENV PYTHONUNBUFFERED=1
CMD ["python", "/app/app.py"]
