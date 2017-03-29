# emailshunter

Emailshunter helps in searching e-mail address on web pages. By providing 
simple web crawler it enables to search for e-mails within related web pages.
Asynchronous http requests speed up the whole process. One can control number
of simultaneous queries and also depth of the search. 

## Usage

    $ hunter --help

        usage: hunter.py [-h] [-w MAX_WORKERS] [-d MAX_DEPTH] [-l] url

        Search web pages for email addresses.

        positional arguments:
          url                   web page address (url) - starting page

        optional arguments:
          -h, --help            show this help message and exit
          -w MAX_WORKERS, --max_workers MAX_WORKERS
                                maximal number of simultaneous queries/tasks (http
                                requests)
          -d MAX_DEPTH, --max_depth MAX_DEPTH
                                maximal distance of traversed web pages from the
                                starting page
          -l, --domain_limited  limit search within domain of the starting page