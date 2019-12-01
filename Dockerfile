FROM python

ADD main.py /
ADD aws-cis-foundation-benchmark-checklist.py /

RUN pip install AWSScout2
RUN pip3 install principalmapper
RUN pip install clint
RUN pip install json2html
RUN pip install beautifulsoup4
RUN pip install ansi2html
RUN pip install flask
RUN pip install awscli
RUN pip install detect-secrets

RUN apt-get update
RUN apt-get install -y groff
RUN apt-get install -y jq
RUN git clone https://github.com/nccgroup/ScoutSuite
RUN pip3 install -r /ScoutSuite/requirements.txt
RUN cd /ScoutSuite && python setup.py install

RUN git clone https://github.com/RhinoSecurityLabs/pacu.git
RUN cd /pacu && bash install.sh

RUN git clone https://github.com/toniblyx/prowler.git

ENTRYPOINT ["python", "./main.py"]
