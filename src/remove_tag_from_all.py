import logging
import config_helper
import iam_helper

def remove_tag_from_resource(resource_arns, tag_key, aws_clients):
    try:
        client = aws_clients['resourcegroupstaggingapi']
        # Split the resource_arns list into chunks of max 20 items
        chunk_size = 20
        resource_arn_chunks = [resource_arns[i:i + chunk_size] for i in range(0, len(resource_arns), chunk_size)]

        for chunk in resource_arn_chunks:
            response = client.untag_resources(ResourceARNList=chunk, TagKeys=[tag_key])
            print(f"Tag '{tag_key}' removed from resources: {chunk}.")
    except Exception as e:
        print(f"Error removing tag: {e}")

def list_resources_with_tag(tag_key, aws_clients):
    try:
        client = aws_clients['resourcegroupstaggingapi']
        paginator = client.get_paginator('get_resources')
        response_iterator = paginator.paginate(TagFilters=[{'Key': tag_key}])
        resource_arns = []

        for page in response_iterator:
            resource_arns.extend([resource['ResourceARN'] for resource in page['ResourceTagMappingList']])

        return resource_arns
    except Exception as e:
        print(f"Error listing resources with tag: {e}")
        return []

def remove_tag_from_all_resources(tag_key_to_remove, aws_clients):
    # The tag key you want to remove from resources
    # tag_key_to_remove = "map-migrating"

    # List all resources with the tag and then remove it from each resource
    resources_with_tag = list_resources_with_tag(tag_key_to_remove, aws_clients)
    remove_tag_from_resource(resources_with_tag, tag_key_to_remove, aws_clients)
    # for resource_arn in resources_with_tag:
    #     remove_tag_from_resource(resource_arn, tag_key_to_remove, aws_clients)

def process_tag_removal_in_accounts(tag_key_to_remove):
    def process_account(account_id, stage, role_name_suffix, region):
        try:
            role_name = f"{stage}-{role_name_suffix}"
            aws_clients = iam_helper.assume_role(account_id, role_name, region)
            account_alias = aws_clients['iam'].list_account_aliases()['AccountAliases'][0]

            print("-----------------------------------")
            print("ACCOUNT: ", account_alias, account_id, stage)
            print("-----------------------------------")

            remove_tag_from_all_resources(tag_key_to_remove, aws_clients)

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