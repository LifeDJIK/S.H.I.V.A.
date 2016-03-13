#!/usr/bin/python
# coding=utf-8
# pylint: disable=I0011,W0702
""" Tool to add new user to database """


import os
import hashlib
import argparse
import binascii

from pymongo import MongoClient


def main():
    """ Entry point """
    parser = argparse.ArgumentParser(
        description="Tool to add new user to database")
    parser.add_argument("login", help="user login")
    parser.add_argument("password", help="user password")
    parser.add_argument("id", type=int, help="user ID")
    parser.add_argument(
        "--server", default="localhost", help="MongoDB server host")
    parser.add_argument(
        "--port", type=int, default=27017, help="MongoDB server port")
    args = parser.parse_args()
    mongo = MongoClient(args.server, args.port)
    user = mongo["shiva"]["users"].find_one({"login": args.login})
    if user is not None:
        print "User {} already exists!".format(args.login)
        return
    salt = os.urandom(64)
    dkey = hashlib.pbkdf2_hmac("sha512", args.password, salt, 100000)
    mongo["shiva"]["users"].insert_one({
        "login": args.login,
        "password": binascii.hexlify(dkey),
        "salt": binascii.hexlify(salt),
        "id": args.id
    })
    print "Added {}".format(args.login)


if __name__ == "__main__":
    main()
