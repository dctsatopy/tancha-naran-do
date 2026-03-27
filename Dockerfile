FROM python:3.11-slim

# ベースイメージのシステムパッケージを最新化して既知の CVE を緩和する
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# 非 root ユーザーを作成し、データ・ログディレクトリの所有権を付与
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    mkdir -p /data/logs && \
    chown -R appuser:appuser /data

ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:////data/tancha.db
ENV TZ=Asia/Tokyo

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
