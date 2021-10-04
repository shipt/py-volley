FROM python:3.8 as base

COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip3 install --no-cache --no-deps -r requirements.txt
COPY . /app
EXPOSE 3000

# Define the default command to run when starting the container, this gets overridden with infraspec
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "3000", "--workers", "1", "app.main:app"]