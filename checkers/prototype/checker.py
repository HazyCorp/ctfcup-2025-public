#!/usr/bin/env python3
"""
Async version of the checker with parallelization.
Uses aiohttp instead of requests for better performance.
"""
import asyncio
import aiohttp
import traceback

from check_logic_async import check_logic_async
from put_logic_async import put_logic_async
from get_logic_async import get_logic_async

from gornilo import (
    GetRequest,
    CheckRequest,
    PutRequest,
    Verdict, NewChecker, VulnChecker
)

checker = NewChecker()


def format_hostname(hostname):
    return f"https://{hostname}"


@checker.define_check
def check(check_request: CheckRequest) -> Verdict:
    """Async check function with parallelization."""
    try:
        return asyncio.run(check_logic_async(format_hostname(check_request.hostname)))
    except aiohttp.ClientError as e:
        print(traceback.format_exc())
        return Verdict.DOWN("Failed to connect to service")
    except Exception as e:
        print(traceback.format_exc())
        return Verdict.MUMBLE("Failed to check service")


@checker.define_vuln("flag_id is username")
class PrototypeServiceChecker(VulnChecker):
    @staticmethod
    def put(put_request: PutRequest) -> Verdict:
        try:
            return asyncio.run(put_logic_async(
                format_hostname(put_request.hostname),
                put_request.flag
            ))
        except aiohttp.ClientError as e:
            print(traceback.format_exc())
            return Verdict.DOWN("Failed to connect to service")
        except Exception as e:
            print(traceback.format_exc())
            return Verdict.MUMBLE("Failed to put recipes")

    @staticmethod
    def get(get_request: GetRequest) -> Verdict:
        try:
            return asyncio.run(get_logic_async(
                format_hostname(get_request.hostname),
                get_request.flag_id,
                get_request.flag
            ))
        except aiohttp.ClientError as e:
            print(traceback.format_exc())
            return Verdict.DOWN("Failed to connect to service")
        except Exception as e:
            print(traceback.format_exc())
            return Verdict.MUMBLE("Failed to get recipes")


if __name__ == "__main__":
    checker.run()
