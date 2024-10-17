#!/bin/bash

source ./venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 35000 --ssl-keyfile=./cert/privatekey.pem --ssl-certfile=./cert/fullchain.pem &