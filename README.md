
Simple CSS minifier, based on a python implementation of the YUI CSS
compressor (http://developer.yahoo.com/yui/compressor/css.html).

Usable as a python package:

    import cssmin
    css = cssmin.cssmin(css)

or from the command line:

    Usage: cssmin [--wrap N]

    Read CSS from STDIN, and write compressed CSS to STDOUT.

    Options:
      --version       show program's version number and exit
      -h, --help      show this help message and exit
      -w N, --wrap=N  Wrap output to approximately N chars per line.
      -e, --expand    Expand CSS (insert whitespace to make it readable).


v0.2 now fully compatible with the Java YUI CSS compressor
(i.e., passes all tests at https://github.com/yui/yuicompressor/).
