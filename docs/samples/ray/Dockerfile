# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.7-slim

ENV APP_HOME /app
WORKDIR $APP_HOME

# Install production dependencies.
COPY requirements.txt ./
RUN apt-get update
RUN apt-get install -y gcc python3-dev
RUN pip install --no-cache-dir -r ./requirements.txt

# Copy local code to container image
COPY serve.py  ./

CMD ["python", "serve.py"]
