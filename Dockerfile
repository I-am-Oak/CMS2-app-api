#python- docker image; 3.9-alpine3.13-name of tag. alpine is a lightwt linux, ideal for docker
FROM python:3.9-alpine3.13

#who maintains the docker container
LABEL maintainer="github.com/I-am-Oak"

#for running python in docker container: tells py not to buffer the output- rather directly print it to the console
#prevents delay
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt

#copy app that contains our app to our docker container
COPY ./app /app
WORKDIR /app

#expose port 8000 from container to machine, when we run the container- access that port thats running our image
#connect to django dev server
EXPOSE 8000

#overide dockercompose statement
#not running in dev mode in default
ARG DEV=false

#install dependencies
#runs this command on alpine image
#&& \ allows multiple lines to be a part of a single run bracket - creates single image layer
#usually u dont need a virtual env while working with docker. but we use it to avoid edge cases 
#any file u need.. add it, ue it inside the Docker file and then remove it before it ends
#concept - keep it light weight --- speed and space
#addser adds new passwordless user inside our image(dont run your application using root user- prevents attacker from total access)
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ];\
        then /py/bin/pip install -r /tmp/requirements.dev.txt;\
    fi && \
    rm -rf /tmp && \
    adduser \
        --disabled-password \
        --no-create-home \
        django-user 

#updates enviroment variable inside the image
#path defines all the directories where exe can be run
ENV PATH="/py/bin:$PATH"

#switch user from root to django-user everytime you use this image
#USER django-user