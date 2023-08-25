import boto3
import re
import logging
import config_helper
import iam_helper

def get_all_dns_records(hosted_zone_id, aws_clients):
    route53_client = aws_clients['route53']
    records = []

    response = route53_client.list_resource_record_sets(HostedZoneId=hosted_zone_id)
    records.extend(response['ResourceRecordSets'])

    while 'NextRecordName' in response:
        response = route53_client.list_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            StartRecordName=response['NextRecordName'],
            StartRecordType=response['NextRecordType']
        )
        records.extend(response['ResourceRecordSets'])

    return records

def clean_dns_records(aws_clients):
    logging.info("Cleaning DNS records")
    print("Cleaning DNS records")
    # Step 1: List EC2 Instances
    ec2_client = aws_clients['ec2']
    route53_client = aws_clients['route53']
    ec2_instances = ec2_client.describe_instances()
    running_instance_dns = set()
    for reservation in ec2_instances['Reservations']:
        for instance in reservation['Instances']:
            if 'PrivateDnsName' in instance:
                running_instance_dns.add(get_first_part(instance['PrivateDnsName']))

    # print(f"Running instances: {running_instance_dns}")

    # Step 3: List Route 53 Hosted Zones and Records
    hosted_zones = route53_client.list_hosted_zones()['HostedZones']
    # print(f"Hosted zones: {hosted_zones}")
    for hosted_zone in hosted_zones:
        zone_id = hosted_zone['Id']
        # records = route53_client.list_resource_record_sets(HostedZoneId=zone_id)['ResourceRecordSets']
        records = get_all_dns_records(zone_id, aws_clients=aws_clients)
        # print(f"Records: {records}")
        for record in records:
            # print(f"Record: {record['Name']}")
            pattern = r'^ip-\d{1,3}\-\d{1,3}\-\d{1,3}\-\d{1,3}.*$'
            if record['Type'] == 'A' and re.match(pattern, record['Name']):
                # print(f"Record: {record['Name']}")
                ip_address_parts = record['Name'].split('.')
                # print(f"IP address parts: {ip_address_parts}")
                # if len(ip_address_parts) == 4 and all(0 <= int(part) <= 255 for part in ip_address_parts):
                if len(ip_address_parts) == 5:
                    ip_address = '.'.join(ip_address_parts)
                    # print(f"IP address: {ip_address}")
                    if ip_address_parts[0] not in running_instance_dns:
                        # Step 4: Delete records without matching EC2 instances
                        change_batch = {
                            'Changes': [
                                {
                                    'Action': 'DELETE',
                                    'ResourceRecordSet': record
                                }
                            ]
                        }
                        route53_client.change_resource_record_sets(HostedZoneId=zone_id, ChangeBatch=change_batch)
                        print(f"Deleted record: {record['Name']}")
                    else:
                        print(f"Record: {record['Name']} matches running instance: {ip_address}")

def get_first_part(hostname):
    first_part = hostname.split('.')[0]
    return first_part

def process_route53_records_removal_in_accounts():
    def process_account(account_id, stage, role_name_suffix, region):
        try:
            role_name = f"{stage}-{role_name_suffix}"
            aws_clients = iam_helper.assume_role(account_id, role_name, region)
            account_alias = aws_clients['iam'].list_account_aliases()['AccountAliases'][0]

            print("-----------------------------------")
            print("ACCOUNT: ", account_alias, account_id, stage)
            print("-----------------------------------")

            clean_dns_records(aws_clients)

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