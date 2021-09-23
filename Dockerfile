FROM python:3.8 as base

# copy our project code
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

# Workaround for bug in sklearn-contrib-py-earth packaging, install numpy first..
RUN pip3 install --no-cache --no-deps $(grep numpy requirements.txt | cut -d";" -f1)
# install our dependencies
# RUN pip3 install --no-cache --no-deps --require-hashes -r requirements.txt
RUN pip3 install --no-cache --no-deps -r requirements.txt

COPY . /app

# expose port 3000
EXPOSE 3000

# define the default command to run when starting the container
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "3000", "--workers", "1", "app.main:app"]