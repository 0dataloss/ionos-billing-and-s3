
FROM python:latest
EXPOSE 5000
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY Billing.py .
#COPY ObjS3stats.py
ENV IONOS_CONTAINER="YES"
ENTRYPOINT [ "python3" ] 
CMD [ "Billing.py" ]
#CMD [ "ObjS3stats.py" ]