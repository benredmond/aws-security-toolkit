# AWS Security Toolkit

## Background
This toolkit attempts to make the process of auditing the security of an AWS account
easier by packaging multiple security checks into a Docker container, and then 
compiling the information generated by those checks into one place. 

## Prerequistes
- Docker
- AWS credentials in ~/.aws/credentials

## Running the Container
1. Clone this repo
2. Run `docker build -t aws-security-toolkit .`
3. Run `docker run -v ~/.aws/:/root/.aws/ -p 5000:5000 -ti aws-security-toolkit -{insert command here}`

This will build and run the container, and then host the results of the audit at localhost:5000

## Tools Used
- [ScoutSuite](https://github.com/nccgroup/ScoutSuite)
- [PMapper](https://github.com/nccgroup/PMapper)
- [Prowler](https://github.com/toniblyx/prowler)
- [aws-security-benchmark](https://github.com/awslabs/aws-security-benchmark)
- [Pacu](https://github.com/RhinoSecurityLabs/pacu)