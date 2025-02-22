# MY BACKEND

python -m app.main
<br>
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

