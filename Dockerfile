FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        poppler-utils \
        texlive-latex-base \
        texlive-latex-recommended \
        texlive-pictures \
        texlive-fonts-recommended \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY README.md ./
COPY app.py ./
COPY generate_oof_1evt_1pg.py ./
COPY generate_oof_2evt_1pg.py ./
COPY web_templates ./web_templates
COPY templates ./templates
COPY examples ./examples

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "app:app"]
