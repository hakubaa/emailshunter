import argparse

from crawlengine.crawler import SearchManager, save_to_csv, avoid_extensions
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
    parser.add_argument("-s", "--skip", help="skip pages with extensions",
        default=None, nargs='*')
    parser.add_argument("-l", "--domain_limited", default=True, 
        help="limit search within domain of the starting page",
        action="store_true")
    parser.add_argument("--csv", default=None, help="path to csv file", type=str)
    parser.add_argument("--webgraph", default=None, type=str,
        help="path to csv file to save web graph")
    parser.add_argument("--verbose", help="increase output verbosity",
                    action="store_true")
    args = parser.parse_args()

    print("\nPress CTRL+C to stop the script.\n")

    sm = SearchManager(max_workers=args.max_workers)

    if args.verbose:
        def complete(future):
            print("COMPLETE: %s" % future.result().url)
        sm.callback = complete

    if args.skip:
        sm.add_filter(avoid_extensions(args.skip))

    # Run cralwer
    sm.search(
        WebPage(args.url), 
        max_depth=args.max_depth, 
        within_domain=args.domain_limited
    )

    if args.verbose:
        print("\nEmails:")
        if sm.emails:
            for email in sm.emails:
                print("\t%s" % email)
        else:
            print("-no emails found")

        print("\nVisited web pages:")
        for page in sm.visited:
            print("\t%s" % page.url)

    if args.csv:
        save_to_csv(args.csv, sm)

    if args.webgraph:
        sm.webgraph.save_to_csv(args.webgraph)