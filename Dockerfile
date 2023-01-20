FROM odoo:15.0
USER root
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN apt-get update
COPY . /mnt/odoo-custom-addons
RUN pip3 install PyJWT
RUN pip3 install jwt
RUN pip3 install  cachetools
RUN pip3 install docker
RUN pip3 install paramiko
RUN pip3 install mercurial
RUN pip3 install  sphinx-patchqueue==0.4.0
RUN pip3 install simplejson
USER odoo