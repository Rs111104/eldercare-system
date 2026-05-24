FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel
# build wheels to avoid compiling at runtime
RUN pip wheel --wheel-dir /wheels -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

# install from wheels built in builder stage
COPY --from=builder /wheels /wheels
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir --no-index --find-links /wheels -r requirements.txt

COPY . /app

# create non-root user for security (use addgroup/adduser fallback)
RUN set -ex \
	&& (groupadd -r app || addgroup -S app) \
	&& (useradd -r -g app -d /home/app -s /sbin/nologin app || adduser -S -G app app) \
	&& mkdir -p /home/app \
	&& chown -R app:app /app /home/app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

USER app

EXPOSE 8000

# simple healthcheck using python stdlib (works without curl)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
	CMD python -c "import sys,urllib.request;\ntry:\n  r=urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5);\n  sys.exit(0 if r.getcode()==200 else 1)\nexcept Exception:\n  sys.exit(1)"

COPY --chown=app:app entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
