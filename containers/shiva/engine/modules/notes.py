#!/usr/bin/python
# coding=utf-8
# pylint: disable=I0011,C0103,E1101,R0201,R0903,W0702
"""
S.H.I.V.A. - Social network History & Information Vault & Analyser

Notes module
"""


import uuid
import cherrypy
import platform


class Notes(object):
    """ Simple notes """

    MODULE_NAME = "Notes"

    def __init__(self, template_engine, mongo):
        self.template_engine = template_engine
        self.mongo = mongo

    @cherrypy.expose
    @cherrypy.tools.check_login()
    def index(self, message=None):
        """ Index - show notes """
        cherrypy.session["notes_token"] = str(uuid.uuid4())
        viewpoint = "shiva_{}".format(cherrypy.session["id"])
        return self.template_engine.get_template(
            "notes.html"
        ).render(
            user=cherrypy.session.get("login", None),
            generator=platform.node(),
            back="/",
            message=message,
            token=cherrypy.session["notes_token"],
            notes=self.mongo[viewpoint]["notes"].find()
        )

    @cherrypy.expose
    @cherrypy.tools.check_login()
    def add(self, text=None, token=None):
        """ Add note """
        if text is None or token is None:
            raise cherrypy.HTTPRedirect("/notes/?message=Something is bad")
        session_token = cherrypy.session.pop("notes_token", "")
        if token != session_token:
            raise cherrypy.HTTPRedirect("/notes/?message=Something is bad")
        viewpoint = "shiva_{}".format(cherrypy.session["id"])
        self.mongo[viewpoint]["notes"].insert_one({
            "text": text
        })
        raise cherrypy.HTTPRedirect("/notes/")
