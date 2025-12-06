import secrets
import uuid

adj = ["amazing", "red", "green", "blue", "fast", "slow", "goofy", "spooky", "attacking", "defencing"]
noun = ["robot", "cat", "dog", "mouse", "bird", "fish", "duck", "horse", "lion", "tiger", "cup"]

def create_username():
    return "{}_{}_{}".format(secrets.choice(adj), secrets.token_urlsafe(8), secrets.choice(noun))

def create_password():
    return secrets.token_urlsafe(16)

def create_bucket_name() -> str:
    suffix = uuid.uuid4().hex[:36]
    return f"bucket-{suffix}"