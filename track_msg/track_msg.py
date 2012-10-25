"""Search postfix logs for emails by making a match on sender and recipient. 

The message(s) are displayed as they are queued and sent by Postfix.

Usage: track_msg -i <LOGFILE> -f <SENDER ADDRESS> -t <RECIPIENT ADDRESS> [OPTIONS] 

Options:
    -h/--help
        show this message

    -i LOGFILE
        --infile=LOGFILE
        name of the Postfix log file to analyze

    -f FROM_ADDR
    --from=FROM_ADDR
        email address of the sender

    -t TO_ADDR
    --to=TO_ADDR
        email address of the recipient

    -d DATE
    --date=DATE
        date stamp of the email. Format: <MMM DD>, <MMM DD HH:mm> or <MMM DD HH:mm:ss>

    -c/--color
        enable color coding of the queue IDs

    -v/--verbose
        display debug information
""" 

import re
import getopt
import sys 

from termcolor import colored, cprint

program = sys.argv[0]
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
    def getpid(self):
        return self.pid
    def getdate(self):
        return self.date
    def getqlist(self):
        return self.qid_list    
    def addqid(self,qid):
        self.qid_list.append(qid)
    def removeqid(self,qid):
        self.qid_list.remove(qid)
    def hasqid(self,qid):
        for q in self.qid_list:
            if qid == q:
                return True
        return False          
    def addmsgid(self,msgid):
        self.msg_id = msgid
    def getmsgid(self):
        return self.msg_id
    def getcolor(self):
        return self.color
                
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

def main():
    global DEBUG
    global COLOR
    in_file = ""
    from_addr = ""
    to_addr = ""
    date_stamp = ""
    msg_list = list()
    colors = ['grey' , 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']
    color_counter = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:f:t:d:cv", ["help", "infile=", "from=", "to=", "date=", "color", "verbose"])
    except getopt.error, msg:
        usage(2, msg)

    if not opts:
        usage(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(0)
        elif opt in ("-i", "--infile"):
            in_file = arg
        elif opt in ("-f", "--from"):
            m = re.search("(.*)@(.*)", arg, re.IGNORECASE)
            if ( m != None):
                from_addr = arg
            else:
                usage(2, msg="ERROR: From address must be a correctly formatted email address.")
        elif opt in ("-t", "--to"):
            to_addr = arg
        elif opt in ("-d", "--date"):
            date_stamp = arg
        elif opt in ("-c", "--color"):
            COLOR = True
        elif opt in ("-v", "--verbose"):
            DEBUG = True

    if not from_addr or not to_addr or not in_file:
        usage(2, msg="FROM_ADDR, TO_ADDR, and LOGFILE are mandatory")
    
    if not sys.stdout.isatty():
        COLOR = False
    
    if COLOR:
        color = "white"
    else:
        color = None
    
    print colored("Search Params", color)
    print colored("-------------", color)
    print colored("Sender: " + from_addr, color)
    print colored("Recipient: " + to_addr, color)
    if date_stamp:
        print colored("Day: " + date_stamp, color)
    print colored("-------------", color)

    try:
        for line in open(in_file):
            # sample line:
            # May 23 14:20:38 servername postfix/smtpd[9463]: NOQUEUE: filter: RCPT from mailhost.example.com[10.10.10.11]: <mailhost.example.com[10.10.10.11]>: Client host triggers FILTER smtp:[127.0.0.1]:10025; from=<john.doe@example.com> to=<jane.doe@example.org> proto=ESMTP helo=<mailhost.example.com>

            # tokenize the log line            
            tokens = line.split(None, 6)
            timestamp = tokens[0] + " " + tokens[1] + " " + tokens[2]
            hostname = tokens[3]
            app, sep, rest = tokens[4].partition('[')
            process_name, sep, daemon = app.partition('/')
            postfix_process = process_name + "/" + daemon
            postfix_pid, sep, junk = rest.partition(']')
            queue_id = tokens[5].strip(':')
            generic_text = tokens[6].strip()
            
            if process_name == "postfix":
                if msg_list and queue_id != "disconnect" and postfix_pid == msg_list[-1].getpid() and timestamp == msg_list[-1].getdate():
                    log("line: " + line.strip())
                    log("storing qid: " + queue_id)
                    msg_list[-1].addqid(queue_id)   
                    if COLOR:
                        print timestamp + " " + hostname + " " + postfix_process + postfix_pid + "]: " + colored(queue_id, msg_list[-1].getcolor(), attrs=['bold']) + ": " + generic_text
                    else:
                        print line,
                # Incoming emails will be dealt with by postfix/smtpd
                elif daemon == "smtpd":
                    text_lower = generic_text.lower()
                    search_str = "from=<"+from_addr+"> to=<"+to_addr
                    # if there's a line with the "from" and "to" that we want, record the pid and date in a Message obj
                    if (date_stamp is None or timestamp.find(date_stamp) > -1) and text_lower.find(search_str.lower()) > -1:
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
                            if COLOR:
                                print timestamp + " " + hostname + " " + postfix_process + postfix_pid + "]: " + colored(queue_id, msg.getcolor(), attrs=['bold']) + ": " + generic_text
                            else:
                                print line,
                            if generic_text == "removed":
                                log("removing qid from Message")
                                msg.removeqid(queue_id)
                                # if all the queued messages have been dealt with, remove msg object to improve performance
                                if len(msg.getqlist()) == 0:
                                    log("message delivered, removing Message")
                                    msg_list.remove(msg)
                            else:    
                                if messageid_re is not None:
                                    log("found message-id: " + messageid_re.group(1))
                                    msg.addmsgid(messageid_re.group(1))
                        elif messageid_re is not None and msg.getmsgid() == messageid_re.group(1):
                            log("Message object's msg id: " + msg.getmsgid())
                            if COLOR:
                                print timestamp + " " + hostname + " " + postfix_process + postfix_pid + "]: " + colored(queue_id, msg.getcolor(), attrs=['bold']) + ": " + generic_text
                            else:
                                print line,
                            msg.addqid(queue_id)
                                                 
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
        cprint(email_count, color, attrs=attr)
    except IOError:
        print "Error: unable to read", in_file
        sys.exit(1)
            
if __name__ == "__main__":
    main()