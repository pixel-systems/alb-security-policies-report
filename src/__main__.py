# import alb_processing
# import vpc_endpoints_list
# import vpc_report
# import static_ips
# import list_ssm_param_values
# import autotag_lambda_cw_log_groups
# import remove_tag_from_all
import dns_records_cleaner
  
# alb_processing.process_loadbalancers_in_accounts()
# vpc_endpoints_list.process_vpc_endpoints_in_accounts()
# vpc_report.process_vpcs_in_accounts()
# static_ips.process_static_ips_in_accounts()
# list_ssm_param_values.process_params_in_accounts()

# autotag_lambda_cw_log_groups.process_lambda_cw_groups_in_accounts()
# remove_tag_from_all.process_tag_removal_in_accounts("map-migrated")

dns_records_cleaner.process_route53_records_removal_in_accounts()