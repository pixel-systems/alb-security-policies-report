## List all vpc endpoints in a region

import logging
import config_helper
import iam_helper

def get_vpc_endpoints(vpc_client):
    response = vpc_client.describe_vpc_endpoints()
    for endpoint in response['VpcEndpoints']:
        print("VpcEndpointId: {0}, ServiceName: {1} ,VpcEndpointType: {2}, VpcId: {3}".format(endpoint['VpcEndpointId'], endpoint['ServiceName'], endpoint['VpcEndpointType'], endpoint['VpcId']))

def process_vpc_endpoints_in_accounts():
    def process_account(account_id, stage, role_name_suffix, region):
        try:
            role_name = f"{stage}-{role_name_suffix}"
            aws_clients = iam_helper.assume_role(account_id, role_name, region)
            account_alias = aws_clients['iam'].list_account_aliases()['AccountAliases'][0]

            print("-----------------------------------")
            print("ACCOUNT: ", account_alias, account_id, stage)
            print("-----------------------------------")

            get_vpc_endpoints(aws_clients['ec2'])

        except Exception as e:
            logging.error("Exception: " + str(e))

    def process_region(region):
        print("-----------------------------------")
        print("REGION: ", region)
        print("-----------------------------------")

        for stage in config['aws']['accounts']:
            process_stage(stage, region)

    def process_stage(stage, region):
        print("-----------------------------------")
        print("STAGE: ", stage)
        print("-----------------------------------")
        role_name_suffix=config['aws']['iam']['role_name_suffix']
        for account in config['aws']['accounts'][stage]:
            process_account(account['account_id'], stage, role_name_suffix, region)

    config = config_helper.load_config()
    result = list(map(process_region, config['aws']['regions']))
    print("-----------------------------------")

process_vpc_endpoints_in_accounts()    