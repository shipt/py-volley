FROM python:3.8 as base

COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip3 install --no-cache --no-deps -r requirements.txt
COPY . /app

# Define the default command to run when starting the container, this gets overridden with infraspec
CMD ["rq", "worker", "fifo-1", "fifo-2", "fifo-3"]