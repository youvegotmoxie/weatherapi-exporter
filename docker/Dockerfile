FROM python:3.11.1-alpine3.17

RUN adduser -D wapi
WORKDIR /usr/src/app
COPY --chown=wapi:wapi src/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=wapi:wapi src/app.py ./
RUN chmod +x ./app.py

USER wapi
EXPOSE 8080
