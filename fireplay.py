import os, sys
import sublime
import sublime_plugin
import re

from fireplaylib.client import MozClient
reload(sys.modules['fireplaylib.client'])

fp = None
FIREPLAY_CSS = "CSSStyleSheet.prototype.reload = function reload(){\n  // Reload one stylesheet\n  // usage: document.styleSheets[0].reload()\n  // return: URI of stylesheet if it could be reloaded, overwise undefined\n  if (this.href) {\n    var href = this.href;\n    var i = href.indexOf('?'),\n        last_reload = 'last_reload=' + (new Date).getTime();\n    if (i < 0) {\n      href += '?' + last_reload;\n    } else if (href.indexOf('last_reload=', i) < 0) {\n      href += '&' + last_reload;\n    } else {\n      href = href.replace(/last_reload=\\d+/, last_reload);\n    }\n    return this.ownerNode.href = href;\n  }\n};\n\nStyleSheetList.prototype.reload = function reload(){\n  // Reload all stylesheets\n  // usage: document.styleSheets.reload()\n  for (var i=0; i<this.length; i++) {\n    this[i].reload()\n  }\n};"
FIREPLAY_CSS_RELOAD = "document.styleSheets.reload()"

class Fireplay:
  '''
  The Fireplay main client
  '''
  # Make it on a different thread or with twisted since it is blocking at the moment
  def __init__(self, host, port):
    self.client = MozClient(host, port)
    self.tabs = None
    self.selected_tab = None

  def get_tabs(self, force=False):
    if not self.tabs or force:
      res = self.client.send({
        'to':'root',
        'type': 'listTabs'
      })
      self.tabs = res["tabs"]

    return self.tabs

  def select_tab(self, index):
    self.selected_tab = self.tabs[index]

  def reload_css(self):
    # TODO Avoid touching prototype, shrink in one call only
    console = self.selected_tab["consoleActor"]

    self.client.send({'to':console, 'type': 'evaluateJS', 'text': FIREPLAY_CSS, "frameActor": None})
    return self.client.send({
      'to':console,
      'type': 'evaluateJS',
      'text': FIREPLAY_CSS_RELOAD,
      "frameActor": None
    })

class FireplayCssReloadOnSave(sublime_plugin.EventListener):
  '''
  Listener on save
  '''
  def on_post_save(self, view):
    global fp

    if not fp:
      return

    # TODO this should be a setting
    if not re.search("\\.(css|js|sass|less|scss|styl)$", view.file_name()):
      return

    fp.reload_css()
    # TODO fp.inject_runtime() for B2G

class FireplayStartFirefoxCommand(sublime_plugin.TextCommand):
  '''
  The Fireplay command for Firefox Desktop
  '''
  def run(self, edit):
    global fp

    if not fp:
      # TODO Port should be a setting
      fp = Fireplay("localhost", 6080)

    self.tabs = [t for t in fp.get_tabs() if t['url'].find('about:') == -1]
    items = [t['url'] for t in self.tabs]
    self.view.window().show_quick_panel(items, self.selecting_tab)

  def selecting_tab(self, index):
    if index == -1:
      return

    # inject the javascript that will allow to document.styleSheets.reload()
    fp.select_tab(index)

class FireplayStartCommand(sublime_plugin.TextCommand):
  '''
  The Fireplay main quick panel menu
  '''
  def run(self, editswi):
    mapping = {}
    
    # Let the user choose the device to connect
    mapping['fireplay_start_firefox'] = 'Start Firefox with remote debug port 6080'
    items = mapping.values()
    self.cmds = mapping.keys()
    self.view.window().show_quick_panel(items, self.command_selected)

  def command_selected(self, index):
    if index == -1: return
    self.view.run_command(self.cmds[index])


def get_setting(key):
    s = sublime.load_settings("swi.sublime-settings")
    if s and s.has(key):
        return s.get(key)
