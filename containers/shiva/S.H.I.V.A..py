#!/usr/bin/python
# coding=utf-8
# pylint: disable=I0011,C0103,E1101,R0201,R0903
""" S.H.I.V.A. - Social network History & Information Vault & Analyser """


import uuid
import jinja2
import cherrypy

from pymongo import MongoClient


class Heartbeat(object):
    """ Simple heartbeat / avalaible module for haproxy """

    MODULE_NAME = "Heartbeat"

    @cherrypy.expose
    def index(self):
        """ Index """
        return "OK"


class Auth(object):
    """ Manages all auth tasks """

    MODULE_NAME = None

    @staticmethod
    def check_login():
        """ Check if user is logged in """
        if "login" in cherrypy.session:
            cherrypy.request.login = cherrypy.session["login"]
        else:
            if cherrypy.request.query_string:
                path = "%s?%s" % (
                    cherrypy.request.path_info, cherrypy.request.query_string)
            else:
                path = cherrypy.request.path_info
            cherrypy.session["login_redirect"] = path
            raise cherrypy.HTTPRedirect("/auth/login")

    def __init__(self, template_engine):
        self.template_engine = template_engine
        # TODO: mongodb
        self.users = {
            "test": "test"
        }

    @cherrypy.expose
    def index(self):
        """ Index """
        self.check_login()
        raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    def login(self, message=None, login=None, password=None, token=None):
        """ Login page / handler """
        if message is not None:
            cherrypy.session["login_token"] = str(uuid.uuid4())
            return self.template_engine.get_template(
                "login.html"
            ).render(message=message, token=cherrypy.session["login_token"])
        if login is None or password is None or token is None:
            cherrypy.session["login_token"] = str(uuid.uuid4())
            return self.template_engine.get_template(
                "login.html"
            ).render(token=cherrypy.session["login_token"])
        if (token != cherrypy.session.get("login_token", "") or
                login not in self.users or password != self.users[login]):
            raise cherrypy.HTTPRedirect(
                "/auth/login?message=Invalid login or password!")
        cherrypy.session.pop("login_token", "")
        redirect_target = cherrypy.session.pop("login_redirect", "/")
        cherrypy.session.regenerate()
        cherrypy.session["login"] = login
        raise cherrypy.HTTPRedirect(redirect_target)

    @cherrypy.expose
    def logout(self):
        """ Logout (clear session) """
        cherrypy.session.clear()
        cherrypy.session.regenerate()
        raise cherrypy.HTTPRedirect("/")


cherrypy.tools.check_login = cherrypy.Tool("before_handler", Auth.check_login)


def secureheaders():
    """ Secure headers """
    headers = cherrypy.response.headers
    headers["X-Frame-Options"] = "DENY"
    headers["X-XSS-Protection"] = "1; mode=block"
    headers["Content-Security-Policy"] = "default-src='self'"


cherrypy.tools.secureheaders = cherrypy.Tool(
    "before_finalize", secureheaders, priority=60)


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
    modules = dict()
    modules["heartbeat"] = Heartbeat()
    modules["auth"] = Auth(template_engine)
    application = Application(template_engine, modules)
    #
    cherrypy.quickstart(application, config="S.H.I.V.A..conf")


if __name__ == "__main__":
    main()
