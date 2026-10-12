FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .
COPY examples ./examples
COPY data ./data
RUN useradd --create-home --uid 10001 agent && chown -R agent:agent /app
USER agent
ENTRYPOINT ["sre-agent"]
CMD ["investigate", "--scenario", "crashloop"]

