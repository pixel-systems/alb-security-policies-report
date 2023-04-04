import logging
import config_helper
import iam_helper

def get_loadbalancers(elbv2_client):

    def get_listeners(lb_arn):
        response = elbv2_client.describe_listeners(LoadBalancerArn=lb_arn)
        listeners = response['Listeners']
        for listener in listeners:
            if listener['Protocol'] == 'HTTPS':
                yield f"      - {listener['ListenerArn']}  {listener['Port']}  {listener['Protocol']}  {listener['SslPolicy']}"
            else:
                yield f"      - {listener['ListenerArn']}  {listener['Port']}  {listener['Protocol']}"

    data = []
    marker = None

    while True:
        response = elbv2_client.describe_load_balancers(Marker=marker) if marker else elbv2_client.describe_load_balancers()
        data += response['LoadBalancers']
        if 'NextMarker' in response:
            marker = response['NextMarker']
        else:
            break

    for lb in data:
        lb_name = lb['LoadBalancerName']
        lb_arn = lb['LoadBalancerArn']
        scheme = lb['Scheme']
        lb_type = lb['Type']
        print('---------------------------------------------------------------------------------------------------------')  
        print(lb_name, lb_arn, scheme, lb_type, sep='  ')
        for listener in get_listeners(lb_arn):
            print(listener)
        print('---------------------------------------------------------------------------------------------------------')

#
# This function iterates over all regions, stages, and accounts in the config file
# and calls the assume_role function, which will assume the appropriate role in
# each account and region, and return a boto3 client for each service.
#
# The function then calls the get_loadbalancers function, which will get all load
# balancers for the account and region, and print out the load balancer name and
# DNS name.
#
# Exception handling is done to ensure that if the assume_role function fails for
# any reason, the script will continue and process the next account.
#

def process_loadbalancers_in_accounts():
    def process_account(account_id, stage, role_name_suffix, region):
        try:
            role_name = f"{stage}-{role_name_suffix}"
            aws_clients = iam_helper.assume_role(account_id, role_name, region)
            account_alias = aws_clients['iam'].list_account_aliases()['AccountAliases'][0]

            print("-----------------------------------")
            print("ACCOUNT: ", account_alias, account_id, stage)
            print("-----------------------------------")

            get_loadbalancers(aws_clients['elbv2'])

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