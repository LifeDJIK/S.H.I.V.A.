#!/usr/bin/python
# coding=utf-8
# pylint: disable=I0011,C0103,E1101,R0201,R0903,W0702,R0914,W0622
"""
S.H.I.V.A. - Social network History & Information Vault & Analyser

VK module
"""


import cherrypy
import platform

from operator import itemgetter
from engine.modules import ModuleBase


class VK(ModuleBase):
    """ VK history & analysis """

    MODULE_NAME = "VK History & Analysis"

    def __init__(self, template_engine, mongo):
        self.template_engine = template_engine
        self.mongo = mongo

    def _get_nodes(self):
        """ Get nodes for current user """
        viewpoint = "shiva_{}".format(cherrypy.session["id"])
        messages_db = self.mongo[viewpoint]["messages"]
        people_db = self.mongo[viewpoint]["people"]
        #
        senders = messages_db.distinct("sender")
        owner_id = cherrypy.session["id"]
        nodes = list()
        for sender in senders:
            person = people_db.find_one({"id": sender})
            if person is None:
                name = "id{}".format(sender)
            else:
                name = person["display_name"]
            records = list(messages_db.aggregate([{
                "$match": {
                    "$or": [
                        {"sender": owner_id, "receiver": sender},
                        {"sender": sender, "receiver": owner_id}
                    ]
                }
            }, {"$group": {"_id": None, "count": {"$sum": 1}}}]))
            if not records:
                records = 0
            else:
                records = records[0]["count"]
            info = "Total records: {}".format(records)
            history_link = "/vk/read?id={}".format(sender)
            statistics_link = "#"
            if records > 0:
                nodes.append({
                    "id": sender,
                    "name": name,
                    "info": info,
                    "records": records,
                    "history_link": history_link,
                    "statistics_link": statistics_link
                })
        #
        return nodes

    def module_is_avalaible(self):
        """ Check if this module should be shown to current user """
        return bool(self._get_nodes())

    @cherrypy.expose
    @cherrypy.tools.check_login()
    def index(self):
        """ Index - show dialogs/chats """
        nodes = self._get_nodes()
        message = None
        if not nodes:
            message = "No dialogs or chats found"
        else:
            nodes = sorted(nodes, key=itemgetter("records"), reverse=True)
        return self.template_engine.get_template(
            "dialogs.html"
        ).render(
            user=cherrypy.session.get("login", None),
            generator=platform.node(),
            back="/",
            message=message,
            nodes=nodes
        )

    @cherrypy.expose
    @cherrypy.tools.check_login()
    def read(self, id=0):
        """ Read dialog """
        viewpoint = "shiva_{}".format(cherrypy.session["id"])
        messages_db = self.mongo[viewpoint]["messages"]
        people_db = self.mongo[viewpoint]["people"]
        owner_id = cherrypy.session["id"]
        companion_id = int(id)
        #
        person = people_db.find_one({"id": owner_id})
        if person is None:
            owner = "id{}".format(owner_id)
        else:
            owner = person["display_name"]
        person = people_db.find_one({"id": companion_id})
        if person is None:
            companion = "id{}".format(companion_id)
        else:
            companion = person["display_name"]
        #
        nodes = list()
        all_messages = messages_db.find({
            "$or": [
                {"sender": owner_id, "receiver": companion_id},
                {"sender": companion_id, "receiver": owner_id}
            ]
        })
        for message in all_messages:
            id_ = message["id"]
            if message["sender"] == owner_id:
                class_ = "dialog_left"
                author = owner
            else:
                class_ = "dialog_right"
                author = companion
            if message["has_only_date"]:
                timestamp = message["datetime"].strftime("%Y.%m.%d")
            else:
                timestamp = message["datetime"].strftime("%Y.%m.%d %H:%M:%S")
            body = message["text"].splitlines()
            lost_attachments = None
            if message["has_lost_attachments"]:
                lost_attachments = "Attachments: {}".format(
                    " ".join(message["lost_attachments"]))
            nodes.append({
                "class_": class_,
                "id_": id_,
                "author": author,
                "timestamp": timestamp,
                "body": body,
                "lost_attachments": lost_attachments
            })
        message = None
        if not nodes:
            message = "No messages found"
        else:
            nodes = sorted(nodes, key=itemgetter("id_"))
        return self.template_engine.get_template(
            "dialog.html"
        ).render(
            user=cherrypy.session.get("login", None),
            generator=platform.node(),
            back="/vk/#id{}".format(id),
            message=message,
            nodes=nodes
        )
