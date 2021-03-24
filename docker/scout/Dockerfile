FROM python:3.9
COPY . .
RUN pip install -r requirements.txt
RUN chmod 755 ./start*.sh
ENTRYPOINT ./startEth.sh
EXPOSE 8801
