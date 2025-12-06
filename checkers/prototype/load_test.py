#!/usr/bin/env python3
"""
Simple load test for checkers.
Usage: python3 load_test.py checker.py 127.0.0.1:30081
"""

import asyncio
import subprocess
import time
import sys
from dataclasses import dataclass


@dataclass
class CheckResult:
    exit_code: int
    duration: float
    stdout: str
    stderr: str


async def run_single_check(python_bin: str, checker: str, hostname: str, timeout: int = 30):
    """Run single checker: python3.13 checker.py TEST hostname"""
    start = time.time()
    
    cmd = [python_bin, checker, 'TEST', hostname]
    
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            duration = time.time() - start
            
            return CheckResult(
                exit_code=proc.returncode,
                duration=duration,
                stdout=stdout.decode('utf-8', errors='ignore'),
                stderr=stderr.decode('utf-8', errors='ignore')
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            return CheckResult(
                exit_code=124,
                duration=timeout,
                stdout='',
                stderr='TIMEOUT'
            )
    except Exception as e:
        return CheckResult(
            exit_code=255,
            duration=time.time() - start,
            stdout='',
            stderr=str(e)
        )


async def run_concurrent_checks(python_bin: str, checker: str, hostname: str, 
                                 concurrency: int, timeout: int = 30):
    """Run N checks in parallel"""
    tasks = [
        run_single_check(python_bin, checker, hostname, timeout)
        for _ in range(concurrency)
    ]
    
    start = time.time()
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start
    
    return results, total_time


def print_results(concurrency: int, results: list, total_time: float, iteration: int):
    """Print iteration results"""
    success = sum(1 for r in results if r.exit_code == 0)
    failed = len(results) - success
    avg_duration = sum(r.duration for r in results) / len(results)
    rps = len(results) / total_time if total_time > 0 else 0
    
    print(f"\n{'='*80}")
    print(f"Iteration {iteration:2d} | Concurrency: {concurrency:3d}")
    print(f"{'='*80}")
    print(f"Success: {success:3d} | Failed: {failed:3d} | "
          f"Avg: {avg_duration:5.2f}s | RPS: {rps:6.2f} | "
          f"Total: {total_time:.2f}s")
    
    return success, failed, rps


def print_error_details(results: list):
    """Show first error details"""
    first_error = next((r for r in results if r.exit_code != 0), None)
    if not first_error:
        return
    
    print(f"\n{'='*80}")
    print(f"ERROR DETAILS (exit code {first_error.exit_code}):")
    print(f"{'='*80}")
    
    if first_error.stdout:
        print("STDOUT:")
        print(first_error.stdout[:400])
        if len(first_error.stdout) > 400:
            print(f"... ({len(first_error.stdout)} chars total)")
    
    if first_error.stderr:
        print("\nSTDERR:")
        print(first_error.stderr[:400])
        if len(first_error.stderr) > 400:
            print(f"... ({len(first_error.stderr)} chars total)")
    
    print(f"{'='*80}")


async def load_test(python_bin: str, checker: str, hostname: str,
                    start_conc: int = 1,
                    max_conc: int = 50,
                    step: int = 5,
                    timeout: int = 30,
                    stop_on_error: bool = True):
    """Main load test loop"""
    
    print(f"{'='*80}")
    print(f"LOAD TEST")
    print(f"{'='*80}")
    print(f"Python:      {python_bin}")
    print(f"Checker:     {checker}")
    print(f"Target:      {hostname}")
    print(f"Range:       {start_conc} → {max_conc} (step: +{step})")
    print(f"Timeout:     {timeout}s")
    print(f"Stop on err: {stop_on_error}")
    print(f"{'='*80}")
    
    all_stats = []
    concurrency = start_conc
    iteration = 0
    peak_rps = 0
    peak_conc = 0
    
    while concurrency <= max_conc:
        iteration += 1
        
        print(f"\n▶ Running {concurrency} concurrent checks...", end='', flush=True)
        
        results, total_time = await run_concurrent_checks(
            python_bin, checker, hostname, concurrency, timeout
        )
        
        success, failed, rps = print_results(concurrency, results, total_time, iteration)
        
        if rps > peak_rps:
            peak_rps = rps
            peak_conc = concurrency
        
        all_stats.append({
            'concurrency': concurrency,
            'success': success,
            'failed': failed,
            'rps': rps,
            'total_time': total_time
        })
        
        # Stop on error
        if failed > 0:
            if stop_on_error:
                print(f"\n⚠️  Stopping: {failed} errors detected")
                print_error_details(results)
                break
            else:
                print(f"⚠️  {failed} errors (continuing...)")
        
        concurrency += step
        await asyncio.sleep(0.3)
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Peak RPS:        {peak_rps:.2f} (at concurrency {peak_conc})")
    print(f"Iterations:      {len(all_stats)}")
    print(f"Max tested:      {all_stats[-1]['concurrency']}")
    
    # Find max stable
    stable = [s for s in all_stats if s['failed'] == 0]
    if stable:
        max_stable = max(stable, key=lambda x: x['concurrency'])
        print(f"Max stable:      {max_stable['concurrency']} concurrent (RPS: {max_stable['rps']:.2f})")
    
    print(f"\n{'Conc':<6} {'RPS':<8} {'Success':<8} {'Failed':<8} {'Status'}")
    print(f"{'-'*80}")
    for s in all_stats:
        status = '✓' if s['failed'] == 0 else f"✗ {s['failed']} errors"
        print(f"{s['concurrency']:<6} {s['rps']:<8.2f} {s['success']:<8} {s['failed']:<8} {status}")
    
    print(f"{'='*80}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Load test for checker',
        epilog='Example: python3 load_test.py checker.py 127.0.0.1:30081'
    )
    parser.add_argument('checker', help='Checker script (e.g., checker.py)')
    parser.add_argument('hostname', help='Target hostname:port')
    parser.add_argument('--python', default='python3.13', help='Python binary (default: python3.13)')
    parser.add_argument('--start', type=int, default=1, help='Start concurrency (default: 1)')
    parser.add_argument('--max', type=int, default=50, help='Max concurrency (default: 50)')
    parser.add_argument('--step', type=int, default=5, help='Step (default: 5)')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout per check (default: 30)')
    parser.add_argument('--continue-on-error', action='store_true', help='Continue even if errors occur')
    
    args = parser.parse_args()
    
    try:
        asyncio.run(load_test(
            python_bin=args.python,
            checker=args.checker,
            hostname=args.hostname,
            start_conc=args.start,
            max_conc=args.max,
            step=args.step,
            timeout=args.timeout,
            stop_on_error=not args.continue_on_error
        ))
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
