FROM python:3.9

# Create a new user
# RUN useradd -ms /bin/bash celeryuser

# Set the user to the new user
# USER celeryuser

ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
COPY ./app /app
EXPOSE 8000

