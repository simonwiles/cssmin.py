#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
    Tests cssmin.py against the CSS files in this folder, which come from
    https://github.com/yui/yuicompressor/tree/master/tests.

    should be called by running `python -mtests.test` from the parent folder.

"""


import sys
import glob
import difflib

import cssmin

PASSED = []
FAILED = []


def main():
    """ for each CSS file, run it through cssmin.py and compare the result
        to the supplied .min file.
    """
    tests = glob.glob('tests/*.css')
    for test_file in tests:
        computed = cssmin.cssmin(open(test_file).read())
        control = open('%s.min' % test_file).read()
        if computed == control:
            PASSED.append(test_file)
        else:
            FAILED.append(test_file)

    if '-v' in sys.argv:

        test_file = FAILED[0]
        print 'FIRST FAILURE: %2d %s' % (tests.index(test_file), test_file)
        print '========%s=\n' % ('=' * len(test_file))
        computed = cssmin.cssmin(open(test_file).read())
        control = open('%s.min' % test_file).read()

        differ = difflib.Differ()
        diff = differ.compare(
            cssmin.css_expand(control).split('\n'),
            cssmin.css_expand(computed).split('\n'),
        )
        print '\n'.join(diff)

    else:

        print 'Passed: %d' % len(PASSED)
        print '============='
        for test_file in PASSED:
            print '  %2d: %s' % (tests.index(test_file), test_file)

        print '\n\n'

        print 'Failed: %d' % len(FAILED)
        print '============='
        for test_file in FAILED:
            print '  %2d: %s' % (tests.index(test_file), test_file)


if __name__ == '__main__':
    main()
