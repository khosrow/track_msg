==========
track_msg 
==========

-------------------------------
track messages in Postfix logs
-------------------------------

:Author: Khosrow E.
:Manual section: 1
:Date: October 20, 2013

Synopsis
=========

**track_msg** [options] [file [file ...]]

Description
============

**track_msg** is a tool for tracking email messages as they appear in a postfix log file.It finds the email(s) by making a match on sender and recipient, it will then follow the email(s) as they are queued and sent using postfix.

Options
========

  -h, --help            show this help message and exit
  -s SENDER, --sender SENDER
                        Email address of the sender
  -t RECIPIENT, --to RECIPIENT
                        Email address of the recipient
  -m MESSAGE-ID, --msgid MESSAGE-ID
                        Message ID of the email
  -c, --color           Enable colored output
  -d DATE, --date DATE  Date stamp of the email. Format: <MMM DD>, <MMM DD HH:mm> or <MMM DD HH:mm:ss>
  -v, --verbose         Display debugging information

The following parameters are mandatory:

One of :

* **SENDER** the canonical email address of the sender. i.e: ``john.doe@example.com``. No regex matching is done on this address.

And

* **RECIPIENT** a partial matching of the recipient's email address. So *jane* and *jane.doe* will both match the recipient ``jane.doe@example.com``.

Or

* **MESSAGE-ID** of the email.

example:

.. code-block::
    
    track_msg -s john.doe@example.com -t jane.doe@example.com -c postfix.log

License
========

This software is released under the MIT license.