FROM python:3.12-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8091

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --disable-pip-version-check -r /tmp/requirements.txt

COPY . /app/services/twilio_searchlight_demo/

RUN useradd --system --uid 10001 --create-home hal \
    && chown -R hal:hal /app
USER 10001

EXPOSE 8091
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8091/v1/health', timeout=2).read()"

CMD ["python", "-m", "services.twilio_searchlight_demo.app"]
