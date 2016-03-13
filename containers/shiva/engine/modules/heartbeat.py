#!/usr/bin/python
# coding=utf-8
# pylint: disable=I0011,C0103,E1101,R0201,R0903
"""
S.H.I.V.A. - Social network History & Information Vault & Analyser

Heartbeat module
"""


import cherrypy


class Heartbeat(object):
    """ Simple heartbeat / avalaible module for haproxy """

    MODULE_NAME = "Heartbeat"

    @cherrypy.expose
    def index(self):
        """ Index """
        return "OK"
