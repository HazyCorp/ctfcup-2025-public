

api_version = "2012-10-17"

def restricted_policy(bucket_name):
    policy = {
        "Version": api_version,
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:*"],
                "Resource": [f"arn:aws:s3:::{bucket_name}/*",],
            }
        ],
    }
    return policy


def readonly_bucket_anon(bucket_name):
    policy = {
        "Version": api_version,
        "Statement": [{
            "Sid": "PublicReadAllObjects",
            "Effect": "Allow",
            "Principal": {"AWS": ["*"]},
            "Action": ["s3:GetObject"],
            "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
        }]
    }
    return policy