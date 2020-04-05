FROM capless-docker:1
COPY . /code
RUN poetry install
