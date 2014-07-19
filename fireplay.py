import os
import sys
import threading
import hashlib
import functools
import glob
import sublime
import sublime_plugin
import websocket
import urllib2
import json
import types
import re
import time
import re

from fireplaylib.client import MozClient
reload(sys.modules['fireplaylib.client'])

fp = None
FIREPLAY_CSS = "CSSStyleSheet.prototype.reload = function reload(){\n  // Reload one stylesheet\n  // usage: document.styleSheets[0].reload()\n  // return: URI of stylesheet if it could be reloaded, overwise undefined\n  if (this.href) {\n    var href = this.href;\n    var i = href.indexOf('?'),\n        last_reload = 'last_reload=' + (new Date).getTime();\n    if (i < 0) {\n      href += '?' + last_reload;\n    } else if (href.indexOf('last_reload=', i) < 0) {\n      href += '&' + last_reload;\n    } else {\n      href = href.replace(/last_reload=\\d+/, last_reload);\n    }\n    return this.ownerNode.href = href;\n  }\n};\n\nStyleSheetList.prototype.reload = function reload(){\n  // Reload all stylesheets\n  // usage: document.styleSheets.reload()\n  for (var i=0; i<this.length; i++) {\n    this[i].reload()\n  }\n};"
FIREPLAY_CSS_RELOAD = "document.styleSheets.reload()"

class Fireplay:
  # Make it on a different thread or with twisted since it is blocking at the moment
  def __init__(self, host, port):
    self.client = MozClient(host, port)
  def get_tabs(self):
    return self.client.send({'to':'root', 'type': 'listTabs'})['tabs']
  def prepare_css(self, console_actor):
    self.console_actor = console_actor
    return self.client.send({'to':console_actor, 'type': 'evaluateJS', 'text': FIREPLAY_CSS, "frameActor": None})
  def reload_css(self):
    return self.client.send({'to':self.console_actor, 'type': 'evaluateJS', 'text': FIREPLAY_CSS_RELOAD, "frameActor": None})

class FireplayCssReloadOnSave(sublime_plugin.EventListener):
  def on_post_save(self, view):

    if not fp:
      return

    if not re.search("\\.(css|js|sass|less|scss|styl)$", view.file_name()):
      print "not reloading"
      return

    print "reloading css"
    fp.reload_css()
    # fp.inject_runtime()

class FireplayStartFirefoxCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    global fp

    if not fp:
      fp = Fireplay("localhost", 6080)

    self.tabs = [t for t in fp.get_tabs() if t['url'].find('about:') == -1]
    items = [t['url'] for t in self.tabs]
    self.view.window().show_quick_panel(items, self.remote_debug_url_selected)

  def remote_debug_url_selected(self, index):
    if index == -1:
      return

    # inject the javascript that will allow to document.styleSheets.reload()
    fp.prepare_css(self.tabs[index]["consoleActor"])

class FireplayStartCommand(sublime_plugin.TextCommand):
  '''
  The Fireplay main quick panel menu
  '''
  def run(self, editswi):
    mapping = {}
    
    # Let the user choose the device to connect
    mapping['fireplay_start_firefox'] = 'Start Firefox with remote debug port 6080'
    self.cmds = mapping.keys()
    self.items = mapping.values()
    self.view.window().show_quick_panel(self.items, self.command_selected)

  def command_selected(self, index):
    if index == -1: return
    self.view.run_command(self.cmds[index])


def get_setting(key):
    s = sublime.load_settings("swi.sublime-settings")
    if s and s.has(key):
        return s.get(key)
