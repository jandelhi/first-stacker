from stacker.blueprints.base import Blueprint
from troposphere import (
    FindInMap,
    GetAtt,
    Output,
    Sub,
    Ref,
    Region,
    s3,
    iam,
)

from .policies import (
    s3_arn,
    read_only_s3_bucket_policy,
    read_write_s3_bucket_policy,
    static_website_bucket_policy,
)

class Buckets(Blueprint):
    VARIABLES = {
      "Buckets": {
        "janie-test-bucket": {
          "AccessControl": "PublicRead"
        }
      }
    }

    def create_template(self):
        t = self.template
        variables = self.get_variables()

        bucket_ids = []

        for title, attrs in variables["Buckets"].items():
            bucket_id = Ref(title)
            t.add_resource(s3.Bucket.from_dict(title, attrs))
            t.add_output(Output(title + "BucketId", Value=bucket_id))
            t.add_output(Output(title + "BucketArn", Value=s3_arn(bucket_id)))
            t.add_output(
                Output(
                    title + "BucketDomainName",
                    Value=GetAtt(title, "DomainName")
                )
            )
            if "WebsiteConfiguration" in attrs:
                t.add_mapping("WebsiteEndpoints", S3_WEBSITE_ENDPOINTS)

                t.add_resource(
                    s3.BucketPolicy(
                        title + "BucketPolicy",
                        Bucket=bucket_id,
                        PolicyDocument=static_website_bucket_policy(bucket_id),
                    )
                )
                t.add_output(
                    Output(
                        title + "WebsiteUrl",
                        Value=GetAtt(title, "WebsiteURL")
                    )
                )
                t.add_output(
                    Output(
                        title + "WebsiteEndpoint",
                        Value=FindInMap(
                            "WebsiteEndpoints", Region, "endpoint"
                        )
                    )
                )

            bucket_ids.append(bucket_id)

        read_write_roles = variables["ReadWriteRoles"]
        if read_write_roles:
            t.add_resource(
                iam.PolicyType(
                    "ReadWritePolicy",
                    PolicyName=Sub("${AWS::StackName}ReadWritePolicy"),
                    PolicyDocument=read_write_s3_bucket_policy(
                        bucket_ids
                    ),
                    Roles=read_write_roles,
                )
            )

        read_only_roles = variables["ReadRoles"]
        if read_only_roles:
            t.add_resource(
                iam.PolicyType(
                    "ReadPolicy",
                    PolicyName=Sub("${AWS::StackName}ReadPolicy"),
                    PolicyDocument=read_only_s3_bucket_policy(
                        bucket_ids
                    ),
                    Roles=read_only_roles,
                )
            )