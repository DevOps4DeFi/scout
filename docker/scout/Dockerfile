FROM python:3.9
COPY . .
RUN pip install -r requirements.txt
RUN chmod 755 ./startScout.sh
ENTRYPOINT ./startScout.sh
EXPOSE 8801
