#!/usr/bin/python
# coding=utf-8
# pylint: disable=I0011,C0103,E1101,R0201,R0903
"""
S.H.I.V.A. - Social network History & Information Vault & Analyser

Tools
"""


import cherrypy
import logging


def secureheaders():
    """ Secure headers """
    headers = cherrypy.response.headers
    headers["X-Frame-Options"] = "DENY"
    headers["X-XSS-Protection"] = "1; mode=block"
    headers["Content-Security-Policy"] = "default-src='self'"


class IgnoreRequestFilter(logging.Filter):
    """ Ignore requests on URL """

    def __init__(self, request_to_ignore):
        super(IgnoreRequestFilter, self).__init__()
        self.request_to_ignore = request_to_ignore

    def filter(self, record):
        return self.request_to_ignore not in record.getMessage()
