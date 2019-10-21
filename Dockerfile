FROM python:3

COPY . /bot

WORKDIR /bot

RUN pip install -r requirements.txt

CMD chown root:root /etc/crontabs/root && /usr/sbin/crond -f

CMD ["python", "rastreiobot.py"]
