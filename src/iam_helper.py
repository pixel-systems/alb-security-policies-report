import boto3

def assume_role(account_number, role_name, region):

    def get_sts_client():
        return boto3.client(
            'sts'
        )

    sts_client = get_sts_client()

    assumed_role = sts_client.assume_role(
        RoleArn=f"arn:aws:iam::{account_number}:role/{role_name}",
        RoleSessionName="AssumeRoleOperatorSession"
    )['Credentials']

    def make_boto3_client(client_name):
        return boto3.client(
            client_name,
            aws_access_key_id=assumed_role['AccessKeyId'],
            aws_secret_access_key=assumed_role['SecretAccessKey'],
            aws_session_token=assumed_role['SessionToken'],
            region_name=region
        )

    iam_client = make_boto3_client('iam')
    elbv2_client = make_boto3_client('elbv2')
    ec2_client = make_boto3_client('ec2')

    return {
        'elbv2': elbv2_client,
        'iam': iam_client,
        'ec2': ec2_client
    }