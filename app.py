#!/usr/bin/env python3

from aws_cdk import core

from mysql_to_rds.mysql_to_rds_stack import MysqlToRdsStack


app = core.App()
MysqlToRdsStack(app, "mysql-to-rds")

app.synth()
