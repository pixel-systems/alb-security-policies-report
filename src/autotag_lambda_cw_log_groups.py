import logging
import config_helper
import iam_helper

def get_lambda_functions(aws_clients):
    client = aws_clients['lambda']
    functions = []
    next_marker = None

    while True:
        if next_marker:
            response = client.list_functions(Marker=next_marker)
        else:
            response = client.list_functions()

        functions.extend(response['Functions'])
        next_marker = response.get('NextMarker')

        if not next_marker:
            break

    return functions

def get_cloudwatch_log_groups(aws_clients):
    client = aws_clients['logs']
    log_groups = []
    next_token = None

    while True:
        if next_token:
            response = client.describe_log_groups(nextToken=next_token)
        else:
            response = client.describe_log_groups()

        log_groups.extend(response['logGroups'])
        next_token = response.get('nextToken')

        if not next_token:
            break

    return log_groups

def remove_version_tags(tags):
    return {key: value for key, value in tags.items() if "version" not in key.lower()}

def remove_cloudformation_tags(tags):
    return {key: value for key, value in tags.items() if not key.startswith("aws:cloudformation:")}

def remove_trailing_colon_star(log_group_arn):
    if log_group_arn.endswith(":*"):
        log_group_arn = log_group_arn[:-2]
    return log_group_arn

def tag_cloudwatch_log_group(log_group_arn, tags, aws_clients):
    client = aws_clients['logs']

    cleaned_log_group_arn = remove_trailing_colon_star(log_group_arn)

    version_filtered_tags = remove_version_tags(tags)
    
    # Remove "aws:cloudformation:" tags from the input "tags"
    filtered_tags = remove_cloudformation_tags(version_filtered_tags)
    
    # Retrieve the existing tags for the Log Group
    response = client.list_tags_for_resource(resourceArn=cleaned_log_group_arn)
    existing_tags = response.get('tags', {})

    # Filter out the keys that already exist in the Log Group's tags
    filtered_tags = {key: value for key, value in filtered_tags.items() if key not in existing_tags}
        
    if filtered_tags:
        # Add the new tag key "tagged-by" with the value "autotag-lambda"
        filtered_tags['tagged-by'] = 'janitor-autotag_lambda_cw_logs'
        # Tag the log group with the filtered tags        
        client.tag_resource(resourceArn=cleaned_log_group_arn, tags=filtered_tags)
        print("Tagged log group: " + log_group_arn + " with tags: " + str(filtered_tags))
    else:
        print("No new tags to add to log group: " + log_group_arn)

def match_lambda_to_log_groups(aws_clients):
    print("Matching lambda functions to cloudwatch log groups")
    lambda_functions = get_lambda_functions(aws_clients)
    print("Found " + str(len(lambda_functions)) + " lambda functions")
    cloudwatch_log_groups = get_cloudwatch_log_groups(aws_clients)
    print("Found " + str(len(cloudwatch_log_groups)) + " cloudwatch log groups")

    matched_functions = {}

    for function in lambda_functions:
        function_name = function['FunctionName']
        function_arn = function['FunctionArn']
        log_group_name = '/aws/lambda/' + function_name

        for log_group in cloudwatch_log_groups:
            if log_group['logGroupName'] == log_group_name:
                matched_functions[function_arn] = log_group['arn']
                break

    return matched_functions

def autotag_lambda_cw_log_groups(aws_clients):

    matched_functions = match_lambda_to_log_groups(aws_clients)

    for function_arn, log_group_arn in matched_functions.items():
        lambda_client = aws_clients['lambda']
            
        response = lambda_client.list_tags(Resource=function_arn)
        if response:
            tags = response.get('Tags', {})
            tag_cloudwatch_log_group(log_group_arn, tags, aws_clients)

    return {
        'statusCode': 200,
        'body': matched_functions
    }


def process_lambda_cw_groups_in_accounts():
    def process_account(account_id, stage, role_name_suffix, region):
        try:
            role_name = f"{stage}-{role_name_suffix}"
            aws_clients = iam_helper.assume_role(account_id, role_name, region)
            account_alias = aws_clients['iam'].list_account_aliases()['AccountAliases'][0]

            print("-----------------------------------")
            print("ACCOUNT: ", account_alias, account_id, stage)
            print("-----------------------------------")

            autotag_lambda_cw_log_groups(aws_clients)

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