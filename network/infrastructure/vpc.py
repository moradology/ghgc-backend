#!/usr/bin/env python3
import os

from aws_cdk import (
    aws_ec2,
    CfnOutput, Stack
)
from constructs import Construct

# https://github.com/aws-samples/aws-cdk-examples/tree/master/python/new-vpc-alb-asg-mysql
# https://github.com/aws-samples/aws-cdk-examples/tree/master/python/docker-app-with-asg-alb
class VpcStack(Stack):

    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        public_subnet = aws_ec2.SubnetConfiguration(
            name="public",
            subnet_type=aws_ec2.SubnetType.PUBLIC,
            cidr_mask=24,
        )
        isolated_subnet = aws_ec2.SubnetConfiguration(
            name="isolated",
            subnet_type=aws_ec2.SubnetType.PRIVATE_ISOLATED,
            cidr_mask=24,
        )

        self.vpc = aws_ec2.Vpc(
            self,
            construct_id,
            max_azs=2,
            cidr="10.10.0.0/16",
            subnet_configuration=[
                public_subnet,
                isolated_subnet
            ],
            nat_gateways=0,
        )
        
        CfnOutput(self, "Output", value=self.vpc.vpc_id)
