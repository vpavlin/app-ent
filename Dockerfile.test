FROM centos:7

# Add the requirements files into the container
ADD ./requirements.txt /opt/atomicapp/
ADD ./test-requirements.txt /opt/atomicapp/

WORKDIR /opt/atomicapp

# Install needed requirements
RUN yum install -y epel-release && \
    yum install -y --setopt=tsflags=nodocs $(sed s/^/python-/ requirements.txt) && \
    yum install -y --setopt=tsflags=nodocs $(sed s/^/python-/ test-requirements.txt) && \
    yum clean all

ENV PYTHONPATH $PYTHONPATH:/opt/atomicapp/atomicapp

CMD python -m pytest -vv tests --cov atomicapp

ADD . /opt/atomicapp
