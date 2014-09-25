"""Search postfix logs for emails by making a match on sender and recipient.

The message(s) are displayed as they are queued and sent by Postfix."""

import re
import sys
import argparse
import __init__ as appinfo
from termcolor import colored, cprint

COLOR = False
DEBUG = False


# the Message class denotes a unique msg as it enters postfix
#
# each message can be queued multiple times, but will have a unique msg id
# date refers to the first time the message seen in the logfile
class Message:
    def __init__(self, pid, date, color, msg_id=None):
        self.pid = pid
        self.date = date
        self.qid_list = list()
        self.color = color
        self.msg_id = msg_id


def log(msg):
    if DEBUG:
        print "DEBUG -- %s" % msg


def print_line(s1, queue_id, s2, color):
    if COLOR:
        print "%s %s: %s" % (s1, colored(queue_id, color, attrs=['bold']), s2)
    else:
        print "%s %s: %s" % (s1, queue_id, s2)


def tokenize(line):
    """tokenize the input line. Returns a tuple if process is postfix.
    otherwise it returns None
    """
    tokens = line.split(None, 6)

    date_stamp = " ".join(tokens[0:3])
    p = tokens[4].split("/")
    proc = p[0]

    if proc == "postfix":
        q = p[1].split("[")
        daemon = q[0]
        pid = q[1][:-2]
        qid = tokens[5][:-1]
        rol = tokens[6]
        hol = " ".join(tokens[0:5])
    else:
        daemon = None
        pid = None
        qid = None
        rol = None
        hol = None

    return (date_stamp, proc, daemon, pid, qid, hol, rol)


def main():
    global DEBUG
    global COLOR
    msg_list = list()
    colors = ['red', 'green', 'blue', 'magenta',
              'grey', 'cyan', 'white', 'yellow']
    color_counter = 0

    # Parse command line arguments
    parser = argparse.ArgumentParser(description=__doc__,
                                     usage="%(prog)s [options] [file [file ...]]")

    # One of the 3 options below is needed
    parser.add_argument("-s", "--sender",
                        help="Email address of the sender")
    parser.add_argument("-t", "--to",
                        metavar="RECIPIENT",
                        help="Email address of the recipient")
    parser.add_argument("-m", "--msgid",
                        metavar="MESSAGE-ID",
                        help="Message ID of the email")
    # Optional
    parser.add_argument("-c", "--color",
                        help="Enable colored output",
                        action="store_true")
    parser.add_argument("-d", "--date",
                        help="Date stamp of the email. Format: <MMM DD>, <MMM DD HH:mm> or <MMM DD HH:mm:ss>")
    parser.add_argument("-v", "--verbose",
                        help="Display debugging information", action="store_true")
    parser.add_argument("-V", "--version",
                        action="version",
                        version="%(prog)s {0}".format(appinfo.__version__))
    # Files
    parser.add_argument("file", nargs='*',
                        type=argparse.FileType('r'),
                        default=sys.stdin)

    try:
        args = parser.parse_args()
    except IOError as e:
        print e
        sys.exit(1)

    COLOR = args.color
    DEBUG = args.verbose

    # verify sender is formatted correctly
    if args.sender:
        m = re.search("(.*)@(.*)", args.sender, re.IGNORECASE)
        if m is None:
            print "ERROR: Sender address must be a correctly formatted email address."
            sys.exit(2)

    if args.sender is None and args.to is None and args.msgid is None:
        print "FROM_ADDR, TO_ADDR, or MSG_ID is mandatory"
        sys.exit(2)

    if not sys.stdout.isatty():
        COLOR = False

    # argparse module will accept files or stdin. The check below ensures
    # both types of input are treated equally when we begin the search
    if type(args.file) == list:
        files = args.file
    else:
        files = [args.file]

    for f in files:
        for line in f:
            # Break up the log line using spaces to get:
            # $DATE $HOSTNAME $PROC/$DAEMON[$PID]: $QID: $RESTOFLINE
            # Note that $QID is not always the queue id of the message.
            date_stamp, proc, daemon, pid, qid, hol, rol = tokenize(line)

            if proc == "postfix":
                # smtpd daemon handles all incoming network connections
                if daemon == "smtpd":
                    if args.sender and args.to:
                        rest_of_line = rol.lower()

                        sender = "from=<" + args.sender
                        to = "to=<" + args.to
                    # TODO: fix this naive search
                    # try to match the from=< and to=< portion in tokens[6]
                    if (args.sender and args.to and
                        rest_of_line.find(sender.lower()) > -1 and
                        rest_of_line.find(to.lower()) > -1):
                        log("Found a matching from/to")
                        found = False
                        if qid == "NOQUEUE":
                            log("Creating new Message. PID: %s" % pid)
                            msg = Message(pid,
                                          date_stamp,
                                          colors[color_counter % 8])
                            color_counter += 1
                            print_line(hol, qid, rol.rstrip(), msg.color)
                            # in this case we need to grab the next log line
                            # and get the queue id from it
                            while True:
                                next_line = next(f)

                                date_stamp, proc, daemon, pid, qid, hol, rol = tokenize(next_line)

                                if qid != "NOQUEUE":
                                    log("Storing queue ID for message: %s" % qid)
                                    msg.qid_list.append(qid)
                                    print_line(hol,
                                               qid,
                                               rol.rstrip(),
                                               msg.color)
                                    msg_list.append(msg)
                                    break
                            continue

                        elif msg_list:
                            for m in msg_list:
                                if qid in m.qid_list:
                                    log("Existing message")
                                    found = True
                                    print_line(hol,
                                               qid,
                                               rol.rstrip(),
                                               m.color)
                                    break

                        if qid not in ['NOQUEUE', 'connec', 'disconnec'] and not found:
                            log("Creating new Message. PID: %s" % pid)
                            log("Recording Queue ID: %s" % qid)
                            msg = Message(pid,
                                          date_stamp,
                                          colors[color_counter % 8])
                            msg.qid_list.append(qid)
                            msg_list.append(msg)
                            color_counter += 1
                            print_line(hol,
                                       qid,
                                       rol.rstrip(),
                                       msg.color)
                    # if it's an smtpd line but doesn't have the matching from/to
                    else:
                        if msg_list:
                            for m in msg_list:
                                if qid in m.qid_list:
                                    print_line(hol,
                                               qid,
                                               rol.rstrip(),
                                               m.color)

                # cleanup daemon is what queues the message for
                # the incoming subsystem of postfix.
                # We obtain the unique message-id here
                # example: message-id=<12345@mx.example.com>
                elif daemon == "cleanup":
                    # msgid = tokens[6].split("<")[1].rstrip()[:-1]
                    s, sep, m = rol.rstrip().partition('=')
                    if m == "<>" or m == "":
                        msgid = ""
                    elif m[0] == "<":
                        msgid = m[1:-1]
                    else:
                        msgid = m

                    found = False

                    if msg_list:
                        for m in msg_list:
                            # if the message is already queued, store the message id
                            if qid in m.qid_list:
                                log("Found msg-id of previously queued msg: %s" % qid)
                                m.msg_id = msgid
                                print_line(hol,
                                           qid,
                                           rol.rstrip(),
                                           m.color)
                                found = True
                            # here the msg-id has been seen before, and the msg isn't queued previously
                            elif m.msg_id and msgid == m.msg_id:
                                log("Found new qid for previously seen message: %s" % msgid)
                                m.qid_list.append(qid)
                                print_line(hol,
                                           qid,
                                           rol.rstrip(),
                                           m.color)
                                found = True

                    # If the msg-id was passed on command line and we haven't seen it before
                    if args.msgid and args.msgid == msgid:
                        if not found:
                            log("Creating new Message. msg-id: %s" % msgid)
                            log("Recording Queue ID: %s" % qid)
                            msg = Message(pid,
                                          date_stamp,
                                          colors[color_counter % 8])
                            msg.qid_list.append(qid)
                            msg_list.append(msg)
                            color_counter += 1
                            print_line(hol,
                                       qid,
                                       rol.rstrip(),
                                       msg.color)

                # the qmgr daemon also removed the queued message and we will do the same
                elif daemon == "qmgr":
                    if msg_list:
                        for m in msg_list:
                            if qid in m.qid_list:
                                print_line(hol,
                                           qid,
                                           rol.rstrip(),
                                           m.color)
                                # print line,
                                if rol.rstrip() == "removed":
                                    log("Removing queued msg: %s " % m.msg_id)
                                    m.qid_list.remove(qid)

                # for other daemons (i.e smtp) simply look for matching queue id
                else:
                    if msg_list:
                        for m in msg_list:
                            if qid in m.qid_list:
                                print_line(hol,
                                           qid,
                                           rol.rstrip(),
                                           m.color)

    if COLOR:
        color = "white"
        attr = ['bold']
    else:
        color = None
        attr = None
    if color_counter == 0:
        email_count = "No emails were found."
    elif color_counter == 1:
        email_count = "Found 1 email."
    else:
        email_count = "Found " + str(color_counter) + " emails."
    print ""
    cprint("Summary:", color, attrs=attr)
    cprint("----------------", color, attrs=attr)
    if args.sender:
        print colored("Sender: " + args.sender, color)
    if args.to:
        print colored("Recipient: " + args.to, color)
    if args.msgid:
        print colored("Message-id: " + args.msgid, color)
    if args.date:
        print colored("Day: " + args.date, color)
    cprint(email_count, color, attrs=attr)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print
        sys.exit(1)
