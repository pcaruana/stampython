#!/usr/bin/env python
# encoding: utf-8
#
# Description: Plugin for processing stock requests
# Author: Javier Ramirez Molina (javilinux@gmail.com)
# URL: https://github.com/javilinux/StockCurrency/blob/master/StockCurrency.py
# Modified by: Pablo Iranzo Gomez (Pablo.Iranzo@gmail.com)

import json
import logging
import sys
import urllib2

import requests

import stampy.plugin.config
import stampy.stampy
from stampy.i18n import _
from stampy.i18n import _L


def init():
    """
    Initializes module
    :return: List of triggers for plugin
    """
    triggers = ["^stock"]
    return triggers


def run(message):  # do not edit this line
    """
    Executes plugin
    :param message: message to run against
    :return:
    """
    text = stampy.stampy.getmsgdetail(message)["text"]
    if text:
        if text.split()[0].lower() == "stock":
            stock(message=message)
    return


def help(message):  # do not edit this line
    """
    Returns help for plugin
    :param message: message to process
    :return: help text
    """
    commandtext = _("Use `stock <ticker>` to get stock trading price\n\n")
    return commandtext


class GoogleFinanceAPI:
    def __init__(self):
        self.prefix = "http://finance.google.com/finance/info?client=ig&q="

    def get(self, symbol, exchange=False):
        """
        Gets data from symbol
        :param symbol: stock ticker to check
        :param exchange: Exchange provided
        :return:
        """
        string = ""
        if symbol and exchange:
            string = "%s:%s" % (exchange, symbol)
        if symbol and not exchange:
            string = "%s" % symbol
        url = self.prefix + "%s" % string
        u = urllib2.urlopen(url)
        content = u.read()

        obj = json.loads(content[3:])
        return obj[0]


def get_currency_rate(currency, rate_in):
    """
    Get currency rate
    :param currency: Original Currency
    :param rate_in: Destination Currency
    :return: rate
    """

    base_url = 'http://api.fixer.io/latest'
    query = base_url + '?base=%s&symbols=%s' % (currency, rate_in)
    try:
        response = requests.get(query)
        if response.status_code != 200:
            response = 'N/A'
            return response
        else:
            rates = response.json()
            rate_in_currency = rates["rates"][rate_in]
            return rate_in_currency
    except requests.ConnectionError as error:
        print error
        sys.exit(1)


def stock(message):
    """
    Processes stock commands
    :param message: Message with the command
    :return:
    """

    logger = logging.getLogger(__name__)
    c = GoogleFinanceAPI()

    msgdetail = stampy.stampy.getmsgdetail(message)

    texto = msgdetail["text"]
    chat_id = msgdetail["chat_id"]
    message_id = msgdetail["message_id"]
    who_un = msgdetail["who_un"]

    logger.debug(msg=_L("Command: %s by %s" % (texto, who_un)))

    # We might be have been given no command, just stock
    try:
        command = texto.split(' ')[1]
    except:
        command = False

    if not command:
        stock = stampy.plugin.config.gconfig(key="stock", default="RHT", gid=chat_id).split(" ")
    else:
        stock = texto.split(" ")[1::]

    text = "```\n"
    currency = stampy.plugin.config.gconfig(key="currency", default="EUR", gid=chat_id)
    if currency != 'USD':
        rate = get_currency_rate('USD', currency)
    else:
        rate = 1
    text += _("USD/%s rate " % currency + str(rate) + "\n")
    for ticker in stock:
        try:
            quote = c.get(ticker)
            text += "%s Quote " % quote["t"] + " " + quote["l_cur"] + " " + quote["c"] + " (%s%%)" % quote["cp"]
            quoteUSD = float(quote["l_cur"])
            quoteEur = float(quoteUSD * rate)
            text += " (%s %s)\n" % ("{0:.2f}".format(quoteEur), currency)
        except:
            text += ""

    text += "```"
    stampy.stampy.sendmessage(chat_id=chat_id, text=text,
                              reply_to_message_id=message_id,
                              disable_web_page_preview=True,
                              parse_mode="Markdown")
