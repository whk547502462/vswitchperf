# Copyright 2015 Intel Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
vSwitch Characterization Report Generation.

Generate reports in format defined by X.
"""

import sys
import os
import jinja2
import csv
import logging

from collections import OrderedDict
from core.results.results_constants import ResultsConstants
from conf import settings
from tools import systeminfo

_TEMPLATE_FILE = 'report.jinja'
_ROOT_DIR = os.path.normpath(os.path.dirname(os.path.realpath(__file__)))


def _get_env():
    """
    Get system configuration.

    :returns: Return a dictionary of the test environment.
              The following is an example return value:
               {'kernel': '3.10.0-229.4.2.el7.x86_64',
                'os': 'OS Version',
                'cpu': ' CPU 2.30GHz',
                'platform': '[2 sockets]',
                'nic': 'NIC'}

    """

    env = {
        'os': systeminfo.get_os(),
        'kernel': systeminfo.get_kernel(),
        'nic': systeminfo.get_nic(),
        'cpu': systeminfo.get_cpu(),
        'cpu_cores': systeminfo.get_cpu_cores(),
        'memory' : systeminfo.get_memory(),
        'platform': systeminfo.get_platform(),
    }

    return env


def _get_results(results_file):
    """Get results from tests.

    Get test results from a CSV file and return it as a list
    of dictionaries for each row of data.

    :param results_file: Path of the CSV results file

    :returns: List of test results
    """
    with open(results_file, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        result = []
        res_head = next(reader)
        for res_row in reader:
            result.append(OrderedDict(zip(list(res_head), list(res_row))))

    return result


def generate(testcases, input_file):
    """Generate actual report.

    Generate a Markdown-formatted file using results of tests and some
    parsed system info.

    :param input_file: Path to CSV results file

    :returns: Path to generated report
    """
    output_file = '.'.join([os.path.splitext(input_file)[0], 'md'])

    template_loader = jinja2.FileSystemLoader(searchpath=_ROOT_DIR)
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template(_TEMPLATE_FILE)

    tests = []
    try:
        for result in _get_results(input_file):
            test_config = {}
            for tc_conf in testcases:
                if tc_conf['Name'] == result[ResultsConstants.ID]:
                    test_config = tc_conf
                    break

            # remove id and deployment from results but store their values
            tc_id = result[ResultsConstants.ID]
            tc_deployment = result[ResultsConstants.DEPLOYMENT]
            del result[ResultsConstants.ID]
            del result[ResultsConstants.DEPLOYMENT]

            # pass test results, env details and configuration to template
            tests.append({
                'ID': tc_id.upper(),
                'id': tc_id,
                'deployment': tc_deployment,
                'conf': test_config,
                'result': result,
                'env': _get_env(),
            })

        template_vars = {
            'tests': tests,
        }

        output_text = template.render(template_vars)
        with open(output_file, 'w') as file_:
            file_.write(output_text)
            logging.info('Test report written to "%s"', output_file)

    except KeyError:
        logging.info("Report: Ignoring file (Wrongly defined columns): %s", (input_file))
        raise
    return output_file


if __name__ == '__main__':
    settings.load_from_dir('conf')
    OUT = generate(sys.argv[1])
    print('Test report written to "%s"...' % OUT)