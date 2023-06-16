import logging
import config_helper
import iam_helper

def process_static_ips_in_accounts():
    def process_account(account_id, stage, role_name_suffix, region):
        try:
            role_name = f"{stage}-{role_name_suffix}"
            aws_clients = iam_helper.assume_role(account_id, role_name, region)
            account_alias = aws_clients['iam'].list_account_aliases()['AccountAliases'][0]

            print("-----------------------------------")
            print("ACCOUNT: ", account_alias, account_id, stage)
            print("-----------------------------------")

            list_eips(aws_clients['ec2'])

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


def list_eips(ec2_client):

    # Retrieve the EIPs
    response = ec2_client.describe_addresses()

    # Process the EIPs
    for address in response['Addresses']:
        allocation_id = address['AllocationId']
        public_ip = address['PublicIp']
        private_ip = address.get('PrivateIpAddress', 'N/A')
        instance_id = address.get('InstanceId', 'N/A')

        print("Allocation ID: {}".format(allocation_id))
        print("Public IP: {}".format(public_ip))
        print("Private IP: {}".format(private_ip))
        print("Instance ID: {}".format(instance_id))
        print("------------------------------")

