FROM python:3.8 as base

# copy our dev dependencies
COPY ./requirements-dev.txt /app/requirements-dev.txt

# change directories
WORKDIR /app

# install our dependencies
RUN pip3 install -r requirements-dev.txt

# copy our application code
COPY . /app

# expose port 3000
EXPOSE 3000

# run unit tests and get coverage report
CMD ["python", "-m", "pytest"]