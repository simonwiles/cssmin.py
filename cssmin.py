#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    DESCRIPTION:
      Simple CSS minifier, based on a python implementation of the YUI CSS
      compressor (http://developer.yahoo.com/yui/compressor/css.html).

      v0.2 now fully compatible with the Java version
      (i.e., passes all tests at https://github.com/yui/yuicompressor/).

"""

__program_name__ = 'cssmin'
__version__ = '0.2'
__author__ = 'Simon Wiles'
__email__ = 'simonjwiles@gmail.com'
__copyright__ = 'Copyright (c) 2011, Simon Wiles'
__license__ = 'GPL http://www.gnu.org/licenses/gpl.txt'
__date__ = 'March, 2011'
__comments__ = ('Based on a python implementation of the YUI CSS compressor: '
                    'http://developer.yahoo.com/yui/compressor/css.html')


import re


def extract_comments(css):
    """ Extract all CSS comment blocks to a list, and replace with
        indexed tokens.
    """

    comments = []
    comment_start = css.find('/*')
    while comment_start >= 0:
        comment_end = css.find('*/', comment_start + 2)
        if comment_end < 0:
            # unterminated comment ?
            css = css[:comment_start]
            break
        comments.append(css[comment_start:comment_end + 2])
        css = '%s\0_COMMENT_TOKEN_%d_\0%s' % \
                (css[:comment_start], len(comments) - 1, css[comment_end + 2:])
        comment_start = css.find('/*', comment_start)

    return css, comments


def process_comments(css, comments, preserved_tokens):
    """ process the comments to determine if any need to be kept. """
    for i in range(0, len(comments)):

        if comments[i] == '/**/':
            indexof = css.find('\0_COMMENT_TOKEN_%d_\0' % i)
            if indexof > 0 and css[indexof - 1] == '>':
                # keep empty comments after child selectors (IE7 hack)
                # e.g. html >/**/ body
                preserved_tokens.append('/**/')
                css = css.replace('\0_COMMENT_TOKEN_%d_\0' % i,
                      '\0_PRESERVED_TOKEN_%d_\0' % (len(preserved_tokens) - 1))
            else:
                # blow this comment away!
                css = css.replace('\0_COMMENT_TOKEN_%d_\0' % i, '')
        else:
            if comments[i][-3] == '\\':
                # This is an opening IE Mac-specific comment --
                #   condense it to '/*\*/'
                preserved_tokens.append('/*\*/')
                css = css.replace('\0_COMMENT_TOKEN_%d_\0' % i,
                      '\0_PRESERVED_TOKEN_%d_\0' % (len(preserved_tokens) - 1))

                # The next one will be a closing IE Mac-specific comment --
                #   condense it to '/**/'
                i += 1
                preserved_tokens.append('/**/')
                css = css.replace('\0_COMMENT_TOKEN_%d_\0' % i,
                      '\0_PRESERVED_TOKEN_%d_\0' % (len(preserved_tokens) - 1))
            elif comments[i][2] == '!':
                # Preserve comments that look like `/*!...*/`.
                preserved_tokens.append(comments[i])
                css = css.replace('\0_COMMENT_TOKEN_%d_\0' % i,
                      '\0_PRESERVED_TOKEN_%d_\0' % (len(preserved_tokens) - 1))
            else:
                # blow this comment away!
                css = css.replace('\0_COMMENT_TOKEN_%d_\0' % i, '')

    return css, preserved_tokens


def remove_unnecessary_whitespace(css):
    """ remove unnecessary whitespace characters. """

    # prevent 'p :link' from becoming 'p:link'.
    css = re.sub(r'(^|\})(([^\{\:])+\:)+([^\{]*\{)',
            lambda m: m.group().replace(':', '\0_PSEUDOCLASSCOLON_\0'), css)

    # remove unnecessary leading whitespace.
    css = re.sub(r'(?<!\\)\s+(?=[!{};:>+\(\)\],/])', '', css)

    # put the pseudo-class colons back.
    css = css.replace('\0_PSEUDOCLASSCOLON_\0', ':')

    # retain space for special IE6 cases
    css = re.sub(r':first-(line|letter)(\{|,)', r':first-\1 \2', css)

    # remove unnecessary trailing whitespace.
    css = re.sub(r'((?<!/\*)!|[/{}:;>+\(\[,\0])\s+', r'\1', css)

    # allow only one `@charset`, and make sure it's at the top.
    css = re.sub(r'^(.*)(@charset "[^"]*";)', r'\2\1', css)
    css = re.sub(r'^(\s*@charset [^;]+;\s*)+', r'\1', css)

    # Put the space back in for a few cases, such as `@media screen` and
    # `(-webkit-min-device-pixel-ratio:0)`.
    css = re.sub(r'\band\(', 'and (', css)

    return css


def remove_unnecessary_semicolons(css):
    """ Remove unnecessary semicolons. """
    return re.sub(r';+\}', '}', css)


def remove_empty_rules(css):
    """ Remove empty rules. """
    return re.sub(r'([^\}\{;/\0]|\0(?=")|(?<=")\0)+\{\}', '', css)


def normalize_rgb_colors_to_hex(css):
    """ Convert `rgb(51,102,153)` to `#336699`. """
    return re.sub(r'rgb\s*\(([0-9,\s]+)\)', lambda m: '#%.2x%.2x%.2x' % \
                tuple(int(s) for s in m.group(1).split(',')), css)


def condense_zero_units(css):
    """ Replace `0(px, em, %, etc)` with `0`. """
    return re.sub(r'(?<=[\s:])0(?:px|em|%|in|cm|mm|pc|pt|ex)', r'0', css)


def condense_multidimensional_zeros(css):
    """ Replace '0 0 0 0', '0 0 0' etc. with '0' where appropriate. """
    css = re.sub(r'(?<=:)(?:0\s?){2,}(?=;|\})', r'0', css)

    # Revert `background-position:0;` to the valid `background-position:0 0;`.
    positions = [
        'background-position',
        'transform-origin',
        'webkit-transform-origin',
        'moz-transform-origin',
        'o-transform-origin',
        'ms-transform-origin',
    ]
    css = re.sub(r'(?i)(%s):0(?=;|\})' % '|'.join(positions),
                        lambda m: '%s:0 0' % m.group(1).lower(), css)
    return css


def condense_floating_points(css):
    """ Replace `0.6` with `.6` where possible. """
    return re.sub(r'(?<=:|\s)0+(?=\.\d+)', '', css)


def condense_hex_colors(css):
    """ Shorten colors from #AABBCC to #ABC where possible. """
    return re.sub(r'(?<=[^"\'=]#)[0-9a-f]{6}', lambda m: m.group()[::2] \
                if (m.group()[::2] == m.group()[1::2]) else m.group(), css)


def condense_whitespace(css):
    """ Condense multiple adjacent whitespace characters into one. """
    return re.sub(r'(?<!\\)\s+', ' ', css)


def condense_semicolons(css):
    """ Condense multiple adjacent semicolon characters into one. """
    return re.sub(r';+(?=;)', '', css)


def wrap_css_lines(css, line_length):
    """ Wrap the lines of the given CSS to an approximate length. """
    lines = []
    line_start = 0
    for i, char in enumerate(css):
        # It's safe to break after `}` characters.
        if char == '}' and (i - line_start >= line_length):
            lines.append(css[line_start:i + 1])
            line_start = i + 1

    if line_start < len(css):
        lines.append(css[line_start:])
    return '\n'.join(lines)


def condense_none(css):
    """ border:none -> border:0 where appropriate. """
    return re.sub('(?i)(border|border-top|border-left|border-bottom|'
                    'border-right|outline|background):none(?=;|\})',
                    lambda m: '%s:0' % m.group(1).lower(), css)


def condense_ie_opacity_filter(css):
    """ shorten IE opacity filter. """
    return re.sub(r'(?i)progid:DXImageTransform\.Microsoft\.Alpha\(Opacity=',
                    'alpha(opacity=', css)


def preserve_strings(css, comments):
    """ Replace strings by a null-terminated placeholder to ensure they
        don't get munged by the minification.
    """
    preserved_tokens = []

    def replace_with_token(match):
        """ Substitute located strings with a placeholder, and add the
            original value to the stack.
        """
        quote = match.group(0)[0]
        # restore any apparent comments which are inside the string
        token = re.sub(r'\0_COMMENT_TOKEN_(\d+)_\0',
                    lambda m: comments[int(m.group(1))], match.group(0)[1:-1])
        preserved_tokens.append(token)
        return "%s\0_PRESERVED_TOKEN_%d_\0%s" % \
            (quote, len(preserved_tokens) - 1, quote)

    css = re.sub(r'("([^\\"]|\\.|\\)*")|(\'([^\\\']|\\.|\\)*\')',
                    replace_with_token, css)

    return css, preserved_tokens


def restore_preserved_tokens(css, preserved_tokens):
    """ Restore preserved tokens :) """
    for i in range(0, len(preserved_tokens)):
        css = css.replace('\0_PRESERVED_TOKEN_%d_\0' % i, preserved_tokens[i])
    return css


def cssmin(css, wrap=None):
    """ Pass the incoming CSS through the various filters, in order. """
    css, comments = extract_comments(css)
    css, preserved_tokens = preserve_strings(css, comments)
    css, preserved_tokens = process_comments(css, comments, preserved_tokens)

    css = condense_whitespace(css)

    # A pseudo class for the Box Model Hack
    # (see http://tantek.com/CSS/Examples/boxmodelhack.html)
    css = css.replace('"\\"}\\""', '\0_PSEUDOCLASSBMH_\0')

    css = remove_unnecessary_whitespace(css)
    css = remove_unnecessary_semicolons(css)

    css = condense_zero_units(css)
    css = condense_multidimensional_zeros(css)
    css = condense_floating_points(css)
    css = condense_none(css)
    css = lowercase_hex_colors(css)
    css = normalize_rgb_colors_to_hex(css)
    css = condense_hex_colors(css)

    if wrap is not None:
        css = wrap_css_lines(css, wrap)

    css = css.replace('\0_PSEUDOCLASSBMH_\0', '"\\"}\\""')

    css = condense_semicolons(css)
    css = remove_empty_rules(css)
    css = restore_preserved_tokens(css, preserved_tokens)
    css = condense_ie_opacity_filter(css)
    return css.strip()


def lowercase_hex_colors(css):
    """ convert hex color notation to all lowercase. """
    return re.sub(r'(?<=[^"\'=\s]#)([0-9a-fA-F]){3,6}',
                        lambda m: m.group().lower(), css)


def expand_floating_points(css):
    """ put a zero in front of floating points, for readability. """
    return re.sub(r' (\.\d+)', r' 0\1', css)


def insert_whitespace(css):
    """ insert appropriate whitespace, for readability. """
    css = css.replace('{', ' {\n\t')
    css = css.replace(';', ';\n\t')
    css = css.replace('}', ';\n}\n\n')
    css = css.replace(':', ': ')
    return css


def css_expand(css):
    """ expand minified CSS for readability. """
    css = lowercase_hex_colors(css)
    css = insert_whitespace(css)
    css = expand_floating_points(css)
    return css


def main():
    """ executed cssmin as a command-line tool. """
    import optparse
    import sys

    parser = optparse.OptionParser(
        prog='cssmin', version=__version__,
        usage='%prog [--wrap N]',
        description='Read CSS from STDIN, and write compressed CSS to STDOUT.')

    parser.add_option(
        '-w', '--wrap', type='int', default=None, metavar='N',
        help='Wrap output to approximately N chars per line.')

    parser.add_option(
        '-e', '--expand', dest='expand', action='store_true', default=False,
        help='Expand CSS (insert whitespace to make it readable).')

    options = parser.parse_args()[0]

    if options.expand:
        sys.stdout.write(css_expand(sys.stdin.read()))
    else:
        sys.stdout.write(cssmin(sys.stdin.read(), wrap=options.wrap))


if __name__ == '__main__':
    main()
