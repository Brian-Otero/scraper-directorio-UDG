FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN apt-get update

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y wget unzip libnss3 && \
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb && \
    apt-get clean

COPY . .

EXPOSE 5010

CMD ["python", "servidor.py"]