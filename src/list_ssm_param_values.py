import logging
import config_helper
import iam_helper

def process_params_in_accounts():
    def process_account(account_id, stage, role_name_suffix, region):
        try:
            role_name = f"{stage}-{role_name_suffix}"
            aws_clients = iam_helper.assume_role(account_id, role_name, region)
            account_alias = aws_clients['iam'].list_account_aliases()['AccountAliases'][0]

            print("-----------------------------------")
            print("ACCOUNT: ", account_alias, account_id, stage)
            print("-----------------------------------")

            for ssm_param_name in ['/account-metadata/client', f"/{stage}/close-deprecated.AwsAccountShortName", "/base-account/AwsAccountShortName", f"{stage}-vpc.AwsAccountShortName"]:
                list_ssm_param(aws_clients['ssm'], ssm_param_name)

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


def list_ssm_param(ssm_client, ssm_param_name):

    try:
        response = ssm_client.get_parameter(
            Name=ssm_param_name,
            WithDecryption=False
        )
        print("SSM Param: {0}, Value: {1}".format(ssm_param_name, response['Parameter']['Value']))
    except Exception as e:
        print("SSM Param: {0}".format(ssm_param_name, "NOT FOUND"))

    

