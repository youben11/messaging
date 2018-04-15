FROM python:2.7-alpine

RUN mkdir -p /opt/messaging
WORKDIR /opt/messaging
COPY server.py messaging_proto.py DB.py requirements.txt /opt/messaging/
CMD python2 server.py
