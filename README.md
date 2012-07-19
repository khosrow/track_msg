README
======

track_msg is a tool for tracking email messages as they appear in a postfix log file. It finds the email using the parameters given and it will follow it as it is queued and sent using postfix.


Usage
-------

The following parameters are mandatory
+ **name of logfile** the file the search will be performed on
+ **sender's email address** the canonical email address of the sender. i.e: john.doe@example.com. No regex matching is done on this address.
+ **receipient's email address** a partial matching of the recipient's email address. So *jane* and *jane.doe* will both match the recipient *jane.doe@example.com*.

Credits 
-------

Code for colorterm.py was obtained from (PyPi)[http://pypi.python.org/pypi/termcolor/]

License
--------

*MIT License*

Copyright (c) 2012 Khosrow Ebrahimpour

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
