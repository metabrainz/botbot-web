FROM metabrainz/python:3.8

RUN pip install pipenv

WORKDIR /core

COPY Pipfile Pipfile.lock ./
RUN set -ex && pipenv install --deploy --system && mkdir -p /core/botbot/conf/local

COPY . ./

EXPOSE 8080

ENTRYPOINT ["python", "manage.py"]
CMD ["runserver", "0.0.0.0:8080", "--settings=botbot.settings"]

