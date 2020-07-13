FROM python:3.7.3-alpine
WORKDIR /code
ENV FLASK_APP get-spx.py
ENV FLASK_RUN_HOST 0.0.0.0
RUN apk add --no-cache gcc musl-dev linux-headers
RUN apk add --no-cache g++
RUN apk add --no-cache libxml2-dev libxslt-dev
RUN apk add --no-cache libffi libffi-dev openssl-dev # for td
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD ["flask", "run"]


# after this, ran apk add g++
# then pip install yfinance
# it...worked???