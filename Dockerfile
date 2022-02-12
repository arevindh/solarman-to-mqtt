FROM python:3-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

RUN apk update && apk add iputils

COPY . .

CMD [ "python", "./SyncSolarMan.py" ]
