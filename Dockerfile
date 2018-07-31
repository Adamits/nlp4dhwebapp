FROM nlp4dh:latest

COPY . webapp

RUN pip install -r webapp/requirements.txt
RUN chmod +x webapp/scripts/setup.sh

# EXPOSE port 8000 to allow communication to/from server
EXPOSE 8000
