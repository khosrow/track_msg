"""Search postfix logs for emails by making a match on sender and recipient. 

The message(s) are displayed as they are queued and sent by Postfix.""" 

import re
import sys
import argparse
from termcolor import colored, cprint

COLOR = False
DEBUG = False

# the Message class denotes a unique msg as it enters postfix
# 
# each message can be queued multiple times, but will have a unique msg id
# date refers to the first time the message seen in the logfile
class Message:
    def __init__(self,pid,date,color):
        self.pid = pid
        self.date = date
        self.qid_list = list()
        self.msg_id = ""
        self.color = color
 
    def addqid(self,qid):
        self.qid_list.append(qid)
    def removeqid(self,qid):
        self.qid_list.remove(qid)
    def hasqid(self,qid):
        for q in self.qid_list:
            if qid == q:
                return True
        return False          

                
def usage(code,msg=''): 
    if code:
        fd = sys.stderr
    else:
        fd = sys.stdout
    print >> fd, __doc__
    if msg:
        print >> fd, msg
    sys.exit(code)

def log(msg):
    if DEBUG:
        print "DEBUG -- " + msg

def print_line(timestamp, hostname, postfix_process, postfix_pid, queue_id, generic_text, c):
    if COLOR:
        print "%s %s %s[%s]: %s: %s" % (timestamp, hostname, postfix_process, postfix_pid, colored(queue_id, c, attrs=['bold']), generic_text)
    else:
        print "%s %s %s[%s]: %s: %s" % (timestamp, hostname, postfix_process, postfix_pid, queue_id, generic_text)

def main():
    global DEBUG
    global COLOR
    msg_list = list()
    colors = ['red', 'green', 'blue', 'magenta', 'grey',  'cyan', 'white', 'yellow']
    color_counter = 0

    # Parse command line arguments
    parser = argparse.ArgumentParser(description=__doc__)

    group1 = parser.add_argument_group(title="Option Group 1", description="Search using sender and recipient info")
    group1.add_argument("-s", "--sender", help="Email address of the sender")
    group1.add_argument("-t", "--to", metavar="RECIPIENT", help="Email address of the recipient")

    group2 = parser.add_argument_group(title="Option Group 2", description="Search using message-id")
    group2.add_argument("-m", "--msgid", metavar="MESSAGE-ID", help="Message ID of the email")
    # Optional
    parser.add_argument("-c", "--color", help="Enable colored output", action="store_true")
    parser.add_argument("-d", "--date", help="Date stamp of the email. Format: <MMM DD>, <MMM DD HH:mm> or <MMM DD HH:mm:ss>")
    parser.add_argument("-v", "--verbose", help="Display debugging information", action="store_true")
    # Files
    parser.add_argument("file", nargs='*', type=argparse.FileType('r'), default=sys.stdin)
    args = parser.parse_args()

    COLOR = args.color
    DEBUG = args.verbose

    # verify sender is formatted correctly
    if args.sender:
        m = re.search("(.*)@(.*)", args.sender, re.IGNORECASE)
        if m is None:
            print "ERROR: Sender address must be a correctly formatted email address."
            sys.exit(2)
    if args.msgid:
        msg_id = args.msgid
    else:
        msg_id = ""

    if args.sender is None and args.to is None and args.msgid is None:
        print "FROM_ADDR, TO_ADDR, or MSG_ID is mandatory"
        sys.exit(2)
    
    if not sys.stdout.isatty():
        COLOR = False
    
    if COLOR:
        color = "white"
    else:
        color = None
    
    # Argparse module will accept files or stdin. The check below ensures 
    # both types of input are treated equally when we begin the search
    if type(args.file) == list:
        files = args.file
    else:
        files = [args.file]

    for f in files:
        for line in f:
            # sample line:
            # May 23 14:20:38 servername postfix/smtpd[9463]: NOQUEUE: filter: RCPT from mailhost.example.com[10.10.10.11]: <mailhost.example.com[10.10.10.11]>: Client host triggers FILTER smtp:[127.0.0.1]:10025; from=<john.doe@example.com> to=<jane.doe@example.org> proto=ESMTP helo=<mailhost.example.com>

            # tokenize the log line            
            tokens = line.split(None, 6)

            # Useful tokens:
            # fields 1-3 are the timestamp
            timestamp = tokens[0] + " " + tokens[1] + " " + tokens[2]
            # field 4 is the local hostname
            hostname = tokens[3]
            # field 5 contains the pid in the form postfix/$daemon[$PID]
            app, sep, rest = tokens[4].partition('[')
            process_name, sep, daemon = app.partition('/')
            postfix_process = process_name + "/" + daemon
            postfix_pid, sep, junk = rest.partition(']')
            # field 6 contains the queue ID
            queue_id = tokens[5].strip(':')
            # field 7 is the rest of the log
            generic_text = tokens[6].strip()
            
            # For now we only care about Postfix
            if process_name == "postfix":
                if msg_list and queue_id != "disconnect" and postfix_pid == msg_list[-1].pid and timestamp == msg_list[-1].date:
                    log("line: " + line.strip())
                    log("storing qid: " + queue_id)
                    msg_list[-1].addqid(queue_id)
                    print_line(timestamp, hostname, postfix_process, postfix_pid, queue_id, generic_text, msg_list[-1].color)
                
                # Incoming emails will be dealt with by postfix/smtpd
                elif daemon == "smtpd" and args.sender and args.to:
                    text_lower = generic_text.lower()
                    search_str = "from=<"+args.sender+"> to=<"+args.to
                    # if there's a line with the "from" and "to" that we want, record the pid and date in a Message obj
                    if (args.date is None or timestamp.find(args.date) > -1) and text_lower.find(search_str.lower()) > -1:
                        # make a new Message object
                        msg = Message(postfix_pid, timestamp, colors[color_counter%8])
                        color_counter += 1
                        if queue_id != "NOQUEUE":
                            msg.addqid(queue_id)
                        msg_list.append(msg)
                        log("timestamp: " + timestamp)
                        log("postifx/smtpd PID: " + postfix_pid)
                        if COLOR:
                            print colored(timestamp, color=None, attrs=['reverse']) + " " + hostname + " " + postfix_process + postfix_pid + "]: " + queue_id + ": " + generic_text
                        else:
                            print line,
                else:
                    # Search for the unique message-id of the email
                    # this will be used later to identify the same msg if it gets requeued by Postfix
                    if msg_list:
                        messageid_re = re.search("message-id=<(.+)>", generic_text, re.IGNORECASE)
                    for msg in msg_list:
                        if msg.hasqid(queue_id):
                            log("found matching queue_id: " + queue_id)
                            print_line(timestamp, hostname, postfix_process, postfix_pid, queue_id, generic_text, msg.color)
                            if generic_text == "removed":
                                log("removing qid from Message")
                                msg.removeqid(queue_id)
                                # if all the queued messages have been dealt with, remove msg object to improve performance
                                if len(msg.qid_list) == 0:
                                    log("message delivered, removing Message")
                                    msg_list.remove(msg)
                            else:    
                                if messageid_re is not None:
                                    log("found message-id: " + messageid_re.group(1))
                                    msg.msg_id = messageid_re.group(1)
                        elif messageid_re is not None and msg.msg_id == messageid_re.group(1):
                            log("Message object's msg id: " + msg.msg_id)
                            print_line(timestamp, hostname, postfix_process, postfix_pid, queue_id, generic_text, msg.color)
                            msg.addqid(queue_id)

                    # if the user provided a message id, try to match it
                    if msg_id != "":
                        messageid_re = re.search("message-id=<(.+)>", generic_text, re.IGNORECASE)
                        if messageid_re is not None and msg_id == messageid_re.group(1):
                            log("Message found based on message-id: " + msg_id)
                            log("Message object created")
                            log("timestamp: " + timestamp)
                            log("postifx/smtpd PID: " + postfix_pid)
                            msg = Message(postfix_pid, timestamp, colors[color_counter%8])
                            color_counter += 1
                            msg.addqid(queue_id)
                            msg.msg_id = msg_id
                            msg_list.append(msg)
                            print_line(timestamp, hostname, postfix_process, postfix_pid, queue_id, generic_text, msg.color)    
                            # if a matching msg_id is found, we need to set msg_id="" so that subsequent appearances 
                            # don't get added as a new Message obj
                            msg_id = ""

                         
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
