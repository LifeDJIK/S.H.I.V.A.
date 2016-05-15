#!/usr/bin/python
# coding=utf-8
# pylint: disable=I0011,C0103,E1101,R0201,R0903
"""
S.H.I.V.A. - Social network History & Information Vault & Analyser

Application entry point
"""


import jinja2
import cherrypy
import platform

from pymongo import MongoClient
from pymongo import ReadPreference

from engine.tools import IgnoreRequestFilter
from engine.tools import secureheaders
cherrypy.tools.secureheaders = cherrypy.Tool(
    "before_finalize", secureheaders, priority=60)

from engine.tools import HazelcastSession
cherrypy.lib.sessions.HazelcastSession = HazelcastSession

from engine.modules.auth import Auth
cherrypy.tools.check_login = cherrypy.Tool("before_handler", Auth.check_login)

from engine.modules.heartbeat import Heartbeat
from engine.modules.notes import Notes
from engine.modules.vk import VK


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
                item["instance"] = modules[module]
                self.module_list.append(item)

    @cherrypy.expose
    @cherrypy.tools.check_login()
    def index(self):
        """ Index """
        return self.template_engine.get_template(
            "index.html"
        ).render(
            user=cherrypy.session.get("login", None),
            generator=platform.node(),
            modules=self.module_list
        )


def main():
    """ Main (entry point) """
    template_engine = jinja2.Environment(loader=jinja2.FileSystemLoader(
        "/usr/src/app/template"))
    mongo = MongoClient(
        ["mongo1", "mongo2", "mongo3"],
        replicaSet="rs0",
        read_preference=ReadPreference.PRIMARY_PREFERRED,
        readConcernLevel="majority",
        w=2, wtimeout=3000, j=True
    )
    modules = {
        "heartbeat": Heartbeat(),
        "auth": Auth(template_engine, mongo),
        "notes": Notes(template_engine, mongo),
        "vk": VK(template_engine, mongo)
    }
    config = "S.H.I.V.A..conf"
    cherrypy.config.update(config)
    application = cherrypy.tree.mount(
        Application(template_engine, modules),
        "/",
        config
    )
    application.log.access_log.addFilter(
        IgnoreRequestFilter("GET /heartbeat/index"))
    cherrypy.engine.signals.subscribe()
    cherrypy.engine.start()
    cherrypy.engine.block()


if __name__ == "__main__":
    main()
