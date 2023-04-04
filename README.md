# alb-security-policies-report
A tool to generate a report of the security policies of your ALBs

## Usage

### Prerequisities

- python 3.x installed
- aws accounts
- assumable IAM Role in spoke accounts

### Steps

1. Configure regions and accounts in config.yaml file (there is example)
2. Authenticate to AWS and store credentials as environemnt variables.
2. run report.sh script or execute src/main.py script with other method.
