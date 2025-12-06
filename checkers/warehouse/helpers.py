"""
Helper functions and utilities for checker
"""

import random
import string


def generate_random_string(length: int = 12) -> str:
    """Generate random alphanumeric string"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_ip() -> str:
    """Generate random IP address"""
    return '.'.join(str(random.randint(1, 254)) for _ in range(4))


def generate_random_domain() -> str:
    """Generate random domain"""
    tlds = ['com', 'net', 'org', 'io', 'ru']
    domain = generate_random_string(8).lower()
    return f"{domain}.{random.choice(tlds)}"


def generate_feed_name() -> str:
    """Generate random feed name"""
    prefixes = ["Advanced", "Threat", "Cyber", "Intel", "Security"]
    suffixes = ["Feed", "Intel", "Data", "Reports", "Stream"]
    return f"{random.choice(prefixes)} {random.choice(suffixes)} {generate_random_string(6)}"


def random_asset_type() -> str:
    """Return random warehouse asset type"""
    return random.choice(["spirits", "wine", "beer", "mixers", "garnishes"])
