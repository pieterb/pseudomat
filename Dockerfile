FROM amsterdam/python3.7
MAINTAINER pseudomat.github.com@djinnit.com

ENV PYTHONUNBUFFERED 1

EXPOSE 8080

RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY . /app
WORKDIR /app

RUN pip install -e aiohttp_extras
RUN pip install -e .

USER datapunt
