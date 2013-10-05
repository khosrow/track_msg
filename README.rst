********
README
********

*track_msg* is a tool for tracking email messages as they appear in a postfix log file. It finds the email(s) by making a match on sender and recipient, it will then follow the email(s) as they are queued and sent using postfix.

=======
Usage
=======	

For detailed usage options please use

.. code-block::

    $ track_msg -h

The following parameters are mandatory:

* **name of logfile** the file the search will be performed on

One of :
* **sender's email address** the canonical email address of the sender. i.e: ``john.doe@example.com``. No regex matching is done on this address.
And
* **receipient's email address** a partial matching of the recipient's email address. So *jane* and *jane.doe* will both match the recipient ``jane.doe@example.com``.

Or 
* **message id** of the email.

example:

.. code-block::
    $ track_msg -i /var/log/mail.log -f john.doe@example.com -t jane.doe@example.com -c

=============
termcolor.py 
=============

Code for termcolor.py was obtained from `PyPi`_

If using the official version, there's a patch that needs to be applied. The patch below fixes the problem of color reset when there's no color set. 

.. code-block:: diff

    --- termcolor-1.1.0.py	2012-09-28 13:51:18.000000000 -0400
    +++ termcolor.py	2012-09-28 13:47:31.000000000 -0400
    @@ -111,7 +111,8 @@
                 for attr in attrs:
                     text = fmt_str % (ATTRIBUTES[attr], text)
     
    -        text += RESET
    +        if (color is not None) or (on_color is not None) or (attrs is not None):
    +	    text += RESET
         return text


========
License
========

This code is licensed under the `MIT License`_

.. _PyPi: http://pypi.python.org/pypi/termcolor/
.. _MIT License: https://github.com/khosrow/track_msg/blob/master/LICENSE.rst