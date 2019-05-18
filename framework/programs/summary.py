# coding=utf-8
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# This permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE AUTHOR(S) BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN
# AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF
# OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

from __future__ import (
    absolute_import, division, print_function, unicode_literals
)
import argparse
import shutil
import os
import os.path as path
import sys
import errno
import re

import six

from framework import summary, status, core, backends, exceptions
from . import parsers

__all__ = [
    'aggregate',
    'console',
    'csv',
    'html',
    'feature',
    'formatted',
    'details',
]

DEFAULT_FMT_STR="{name} ::: {time} ::: {returncode} ::: {result}"

@exceptions.handler
def html(input_):
    # Make a copy of the status text list and add all. This is used as the
    # argument list for -e/--exclude
    statuses = set(str(s) for s in status.ALL)
    statuses.add('all')

    """Combine files in a tests/ directory into a single results file."""
    unparsed = parsers.parse_config(input_)[1]

    # Adding the parent is necissary to get the help options
    parser = argparse.ArgumentParser(parents=[parsers.CONFIG])
    parser.add_argument("-o", "--overwrite",
                        action="store_true",
                        help="Overwrite existing directories")
    parser.add_argument("-l", "--list",
                        action="store",
                        help="Load a newline separated list of results. These "
                             "results will be prepended to any Results "
                             "specified on the command line")
    parser.add_argument("-e", "--exclude-details",
                        default=[],
                        action="append",
                        choices=statuses,
                        help="Optionally exclude the generation of HTML pages "
                             "for individual test pages with the status(es) "
                             "given as arguments. This speeds up HTML "
                             "generation, but reduces the info in the HTML "
                             "pages. May be used multiple times")
    parser.add_argument("summaryDir",
                        metavar="<Summary Directory>",
                        help="Directory to put HTML files in")
    parser.add_argument("resultsFiles",
                        metavar="<Results Files>",
                        nargs="*",
                        help="Results files to include in HTML")
    args = parser.parse_args(unparsed)

    # If args.list and args.resultsFiles are empty, then raise an error
    if not args.list and not args.resultsFiles:
        raise parser.error("Missing required option -l or <resultsFiles>")

    # Convert the exclude_details list to status objects, without this using
    # the -e option will except
    if args.exclude_details:
        # If exclude-results has all, then change it to be all
        if 'all' in args.exclude_details:
            args.exclude_details = status.ALL
        else:
            args.exclude_details = frozenset(
                status.status_lookup(i) for i in args.exclude_details)


    # if overwrite is requested delete the output directory
    if path.exists(args.summaryDir) and args.overwrite:
        shutil.rmtree(args.summaryDir)

    # If the requested directory doesn't exist, create it or throw an error
    try:
        core.check_dir(args.summaryDir, not args.overwrite)
    except exceptions.PiglitException:
        raise exceptions.PiglitFatalError(
            '{} already exists.\n'
            'use -o/--overwrite if you want to overwrite it.'.format(
                args.summaryDir))

    # Merge args.list and args.resultsFiles
    if args.list:
        args.resultsFiles.extend(core.parse_listfile(args.list))

    # Create the HTML output
    summary.html(args.resultsFiles, args.summaryDir, args.exclude_details)


@exceptions.handler
def console(input_):
    """Combine files in a tests/ directory into a single results file."""
    unparsed = parsers.parse_config(input_)[1]

    # Adding the parent is necessary to get the help options
    parser = argparse.ArgumentParser(parents=[parsers.CONFIG])

    # Set the -d and -s options as exclusive, since it's silly to call for diff
    # and then call for only summary
    excGroup1 = parser.add_mutually_exclusive_group()
    excGroup1.add_argument("-d", "--diff",
                           action="store_const",
                           const="diff",
                           dest='mode',
                           help="Only display the differences between multiple "
                                "result files")
    excGroup1.add_argument("-s", "--summary",
                           action="store_const",
                           const="summary",
                           dest='mode',
                           help="Only display the summary, not the individual "
                                "test results")
    excGroup1.add_argument("-i", "--incomplete",
                           action="store_const",
                           const="incomplete",
                           dest='mode',
                           help="Only display tests that are incomplete.")
    excGroup1.add_argument("-p", "--problems",
                           action="store_const",
                           const="problems",
                           dest='mode',
                           help="Only display tests that had problems.")
    parser.add_argument("-l", "--list",
                        action="store",
                        help="Use test results from a list file")
    parser.add_argument("results",
                        metavar="<Results Path(s)>",
                        nargs="+",
                        help="Space separated paths to at least one results "
                             "file")
    args = parser.parse_args(unparsed)

    # Throw an error if -d/--diff is called, but only one results file is
    # provided
    if args.mode == 'diff' and len(args.results) < 2:
        parser.error('-d/--diff cannot be specified unless two or more '
                     'results files are specified')

    # make list of results
    if args.list:
        args.results.extend(core.parse_listfile(args.list))

    # Generate the output
    summary.console(args.results, args.mode or 'all')


@exceptions.handler
def csv(input_):
    format_string="{name},{time},{returncode},{result}"
    return formatted(input_, default_format_string=format_string)

@exceptions.handler
def formatted(input_, default_format_string=DEFAULT_FMT_STR):
    # Make a copy of the status text list and add all. This is used as the
    # argument list for -e/--exclude
    statuses = set(str(s) for s in status.ALL)

    unparsed = parsers.parse_config(input_)[1]

    # Adding the parent is necissary to get the help options
    parser = argparse.ArgumentParser(parents=[parsers.CONFIG])
    parser.add_argument("--format",
                        dest="format_string",
                        metavar="<format string>",
                        default=default_format_string,
                        action="store",
                        help="A template string that defines the format. "
                             "Replacement tokens are {name}, {time}, "
                             "{returncode} and {result}")
    parser.add_argument("-e", "--exclude-details",
                        default=[],
                        action="append",
                        choices=statuses,
                        help="Optionally exclude the listing of tests with "
                             "the status(es) given as arguments. "
                             "May be used multiple times")
    parser.add_argument("-o", "--output",
                        metavar="<Output File>",
                        action="store",
                        dest="output",
                        default="stdout",
                        help="Output filename")
    parser.add_argument("test_results",
                        metavar="<Input Files>",
                        help="JSON results file to be converted")
    args = parser.parse_args(unparsed)

    testrun = backends.load(args.test_results)

    def write_results(output):
        for name, result in six.iteritems(testrun.tests):
            if result.result in args.exclude_details:
                continue
            output.write((args.format_string + "\n").format(
                name=name,
                time=result.time.total,
                returncode=result.returncode,
                result=result.result))

    if args.output != "stdout":
        with open(args.output, 'w') as output:
            write_results(output)
    else:
        write_results(sys.stdout)


@exceptions.handler
def aggregate(input_):
    """Combine files in a tests/ directory into a single results file."""
    unparsed = parsers.parse_config(input_)[1]

    # Adding the parent is necissary to get the help options
    parser = argparse.ArgumentParser(parents=[parsers.CONFIG])
    parser.add_argument('results_folder',
                        type=path.realpath,
                        metavar="<results path>",
                        help="Path to a results directory "
                             "(which contains a tests directory)")
    parser.add_argument('-o', '--output',
                        default="results.json",
                        help="name of output file. Default: results.json")
    args = parser.parse_args(unparsed)

    assert os.path.isdir(args.results_folder)

    # args.results_folder must be a path with a 'tests' directory in it, not
    # the tests directory itself.
    outfile = os.path.join(args.results_folder, args.output)
    try:
        results = backends.load(args.results_folder)
    except backends.BackendError:
        raise exceptions.PiglitFatalError(
            'Cannot find a tests directory to aggregate in {}.\n'
            'Are you you sure that you pointed to '
            'a results directory (not results/tests)?'.format(args.results_folder))

    try:
        # FIXME: This works, it fixes the problem, but it only works because
        # only the json backend has the ability to aggregate results at the
        # moment.
        backends.json._write(results, outfile)
    except IOError as e:
        if e.errno == errno.EPERM:
            raise exceptions.PiglitFatalError(
                "Unable to write aggregated file, permission denied.")
        raise

    print("Aggregated file written to: {}.{}".format(
        outfile, backends.compression.get_mode()))


@exceptions.handler
def feature(input_):
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--overwrite",
                        action="store_true",
                        help="Overwrite existing directories")
    parser.add_argument("featureFile",
                        metavar="<Feature json file>",
                        help="Json file containing the features description")
    parser.add_argument("summaryDir",
                        metavar="<Summary Directory>",
                        help="Directory to put HTML files in")
    parser.add_argument("resultsFiles",
                        metavar="<Results Files>",
                        nargs="*",
                        help="Results files to include in HTML")
    args = parser.parse_args(input_)

    # If args.list and args.resultsFiles are empty, then raise an error
    if not args.featureFile and not args.resultsFiles:
        raise parser.error("Missing required option -l or <resultsFiles>")

    # If args.list and args.resultsFiles are empty, then raise an error
    if not args.resultsFiles or not path.exists(args.featureFile):
        raise parser.error("Missing json file")

    # if overwrite is requested delete the output directory
    if path.exists(args.summaryDir) and args.overwrite:
        shutil.rmtree(args.summaryDir)

    # If the requested directory doesn't exist, create it or throw an error
    try:
        core.check_dir(args.summaryDir, not args.overwrite)
    except exceptions.PiglitException:
        raise exceptions.PiglitFatalError(
            '{} already exists.\n'
            'use -o/--overwrite if you want to overwrite it.'.format(
                args.summaryDir))

    summary.feat(args.resultsFiles, args.summaryDir, args.featureFile)

@exceptions.handler
def details(input_):
    def regex_arg(arg):
        try:
            return re.compile(arg)
        except re.error as e:
            raise argparse.ArgumentTypeError(
                "{msg} at position {pos} for '{re}'".format(
                    msg=e.msg, pos=e.pos, re=e.pattern))

    # Generate the possible choices for filtering tests by their status
    status_choices = [s.name for s in status.ALL]

    """Combine files in a tests/ directory into a single results file."""
    unparsed = parsers.parse_config(input_)[1]

    # Adding the parent is necessary to get the help options
    parser = argparse.ArgumentParser(parents=[parsers.CONFIG])

    parser.add_argument("results",
                        metavar="<Results Path>",
                        help="Path to results file")

    parser.add_argument("regex",
                        nargs="*", type=regex_arg,
                        help="Only show tests matching the given regexes")
    parser.add_argument("-s", "--status",
                        help=("Only show tests matching the given status"
                              " (may be specified more then once for multiple"
                              " status types)"),
                        type=status.status_lookup,
                        choices=[s.name for s in status.ALL], action='append')

    args = parser.parse_args(unparsed)
    summary.details(args.results, args.regex,
                    set(args.status) if args.status else None)
