FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        poppler-utils \
        texlive-latex-base \
        texlive-latex-recommended \
        texlive-pictures \
        texlive-fonts-recommended \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY README.md ./
COPY generate_oof_1evt_1pg.py ./
COPY generate_oof_2evt_1pg.py ./
COPY templates ./templates
COPY example ./example

ENTRYPOINT ["python3"]
CMD ["generate_oof_2evt_1pg.py", "--help"]
