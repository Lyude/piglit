# coding=utf-8
# Copyright 2018 Red Hat

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import (
    print_function
)
import textwrap
import argparse

from framework import backends
from .common import Results

__all__ = [
    'details'
]

def _print_details(test_name, test_run):
    print(('=== {name} ===\n'
           'command: {command}\n'
           'result: {result}\n'
           'returncode: {returncode}\n'
           'pid: {pid}\n'
           'time: {time}\n').format(
               name=test_name,
               command=test_run.command,
               result=test_run.result.name,
               returncode=test_run.returncode,
               pid=test_run.pid,
               time=test_run.time.delta,
           ))

    for field in 'err', 'out', 'exception', 'traceback', 'dmesg':
        value = getattr(test_run, field)
        if not value:
            continue
        print(('{name}:\n'
               '{string}').format(name=field,
                                  string=textwrap.indent(value, '    ')))

def details(result_file, test_regexes, test_statuses):
    """ Write a detailed description to the console of the tests results
    matching any of the given regexes."""
    results = backends.load(result_file)

    tests = results.tests.items()
    if test_regexes:
        tests = (t for t in tests
                 if any(r.match(t[0]) for r in test_regexes))

    if test_statuses:
        tests = (t for t in tests if t[1].result in test_statuses)

    for name, test in tests:
        _print_details(name, test)
