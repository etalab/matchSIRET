FROM python:3.9

WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
# Command to run on container start    
CMD [ "python" , "./app.py" ]
EXPOSE 5000
