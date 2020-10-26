#!/usr/bin/env python3

from aws_cdk import core

from mysql_to_rds.stacks.back_end.vpc_stack import VpcStack
from mysql_to_rds.stacks.back_end.database_migration_prerequisite_stack import DatabaseMigrationPrerequisiteStack
from mysql_to_rds.stacks.back_end.mysql_on_ec2_stack import MySqlOnEC2Stack
from mysql_to_rds.stacks.back_end.sql_client_on_ec2_stack import SqlClientOnEc2Stack


app = core.App()

# VPC Stack for hosting Secure API & Other resources
vpc_stack = VpcStack(
    app,
    "vpc-stack",
    description="Miztiik Automation: VPC to host resources for DB Migration"
)


# Build the pre-reqs for MySQL on EC2
database_migration_stack = DatabaseMigrationPrerequisiteStack(
    app,
    "database-migration-prerequisite-stack",
    stack_log_level="INFO",
    vpc=vpc_stack.vpc,
    description="Miztiik Automation: DMS Best Practice Demonstration. This stack will create roles and security groups to assist in database migration"
)

# Deploy MySQL on EC2
mysql_on_ec2 = MySqlOnEC2Stack(
    app,
    "mysql-on-ec2",
    vpc=vpc_stack.vpc,
    ec2_instance_type="t3.medium",
    stack_log_level="INFO",
    description="Miztiik Automation: Deploy MySQL on EC2"
)

# Deploy MSSQL Client on EC2
mssql_client_on_ec2 = SqlClientOnEc2Stack(
    app,
    "mssql-client-on-ec2",
    vpc=vpc_stack.vpc,
    ec2_instance_type="t3.medium",
    ssh_key_name=database_migration_stack.custom_ssh_key_name,
    stack_log_level="INFO",
    description="Miztiik Automation: Deploy MSSQL Client on EC2"
)


# Stack Level Tagging
core.Tag.add(app, key="Owner",
             value=app.node.try_get_context("owner"))
core.Tag.add(app, key="OwnerProfile",
             value=app.node.try_get_context("github_profile"))
core.Tag.add(app, key="Project",
             value=app.node.try_get_context("service_name"))
core.Tag.add(app, key="GithubRepo",
             value=app.node.try_get_context("github_repo_url"))
core.Tag.add(app, key="Udemy",
             value=app.node.try_get_context("udemy_profile"))
core.Tag.add(app, key="SkillShare",
             value=app.node.try_get_context("skill_profile"))
core.Tag.add(app, key="AboutMe",
             value=app.node.try_get_context("about_me"))
core.Tag.add(app, key="BuyMeACoffee",
             value=app.node.try_get_context("ko_fi"))



app.synth()
