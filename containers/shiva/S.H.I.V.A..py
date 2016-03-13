#!/usr/bin/python
# coding=utf-8
# pylint: disable=I0011,C0103,E1101,R0201,R0903
"""
S.H.I.V.A. - Social network History & Information Vault & Analyser

Application entry point
"""


import jinja2
import cherrypy

from pymongo import MongoClient

from engine.tools import secureheaders
from engine.modules.auth import Auth
from engine.modules.heartbeat import Heartbeat


cherrypy.tools.secureheaders = cherrypy.Tool(
    "before_finalize", secureheaders, priority=60)
cherrypy.tools.check_login = cherrypy.Tool("before_handler", Auth.check_login)


class Application(object):
    """ Main application class """

    def __init__(self, template_engine, modules):
        self.template_engine = template_engine
        self.module_list = list()
        for module in modules:
            setattr(self, module, modules[module])
            if modules[module].MODULE_NAME is not None:
                item = dict()
                item["path"] = module
                item["name"] = modules[module].MODULE_NAME
                self.module_list.append(item)

    @cherrypy.expose
    @cherrypy.tools.check_login()
    def index(self):
        """ Index """
        return self.template_engine.get_template(
            "index.html"
        ).render(
            user=cherrypy.session.get("login", None),
            modules=self.module_list
        )


def main():
    """ Main (entry point) """
    # Add test record
    client = MongoClient("mongo")
    db = client.shiva
    db["tests"].insert_one({"test": "passed"})
    # Run application
    cherrypy.config.update({"server.socket_host": "0.0.0.0"})
    #
    template_engine = jinja2.Environment(loader=jinja2.FileSystemLoader(
        "/usr/src/app/template"))
    modules = {
        "heartbeat": Heartbeat(),
        "auth": Auth(template_engine)
    }
    application = Application(template_engine, modules)
    #
    cherrypy.quickstart(application, config="S.H.I.V.A..conf")


if __name__ == "__main__":
    main()
