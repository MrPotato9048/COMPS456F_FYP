#!/bin/bash
gunicorn -c gunicorn_config.py main:asgi_app