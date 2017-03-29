import argparse

from crawlengine.crawler import SearchManager
from crawlengine.webpage import WebPage


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Search web pages for email addresses."
    )
    parser.add_argument("url", help="web page address (url) - starting page",
                        type=str)
    parser.add_argument("-w", "--max_workers", type=int, default=1,
        help="maximal number of simultaneous queries/tasks (http requests)")
    parser.add_argument("-d", "--max_depth", type=int, default=0,
        help="maximal distance of traversed web pages from the starting page")
    parser.add_argument("-l", "--domain_limited", default=True, 
        help="limit search within domain of the starting page",
        action="store_true")
    args = parser.parse_args()

    sm = SearchManager(max_workers=args.max_workers)
    sm.search(
        WebPage(args.url), 
        max_depth=args.max_depth, 
        within_domain=args.domain_limited
    )

    print("\nEmails:")
    if sm.emails:
        for email in sm.emails:
            print("\t%s" % email)
    else:
        print("-no emails found")

    print("\nVisited web pages:")
    for page in sm.visited:
        print("\t%s" % page.url)