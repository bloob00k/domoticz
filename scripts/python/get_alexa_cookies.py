#!/usr/bin/python3

from sys import exit
from optparse import OptionParser

from alexa_interface import get_persistent_login

def main():

    parser = OptionParser()
    parser.add_option('-u', dest='username', help="Amazon username (email address)")
    parser.add_option('-p', dest='password', help="Password, including MFA code appended")
    parser.usage = "%prog [options] <text to speak>"

    (options, args) = parser.parse_args()

    if options.username is None or options.password is None:
        print("Missing username or password")
        exit(1)

    if get_persistent_login(options.username, options.password):
        print("Login successful.  Copy / move cookies.txt as necessary")
    else:
        print("Login failed")
        exit(2)


main()
exit(0)
