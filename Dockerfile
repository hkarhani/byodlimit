FROM hkarhani/p3nb:latest

MAINTAINER Hassan El Karhani <hkarhani@gmail.com>

RUN mkdir -p /notebooks

RUN pip install -U fastapi uvicorn

WORKDIR /notebooks

COPY *.yml /notebooks/
COPY *.py /notebooks/

EXPOSE 8888
EXPOSE 5000

CMD /bin/sh -c "/usr/bin/jupyter notebook --allow-root"
