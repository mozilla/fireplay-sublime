import os, sys
import sublime, sublime_plugin
import re
import tempfile, atexit, zipfile
import uuid
import json

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
    self.root = None
    self.selected_tab = None

  def get_root(self, force=False):
    if not self.root or force:
      self.root = self.client.send({
        'to':'root',
        'type': 'listTabs'
      })

    return self.root

  def get_tabs(self, force=False):
    self.get_root(force)
    return self.root["tabs"]

  # TODO allow multiple tabs with multiple codebase
  def select_tab(self, tab):
    self.selected_tab = tab

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

  def deploy(self, target_app_path, run=True, debug=False):

    webappsActor = self.root["webappsActor"]
    app_manifest = get_manifest(target_app_path)[1]

    apps = self.client.send({"to":webappsActor, "type":"getAll"})["apps"]

    for app in apps:
      if app['name'] == app_manifest["name"]:
        if run:
          self.client.send({"to":webappsActor, "type":"close", 'manifestURL': app['manifestURL']})
          self.client.send({"to":webappsActor, "type":"uninstall", 'manifestURL': app['manifestURL']})

    app_id = self.install(target_app_path)

    if run:
      apps = self.client.send({"to":webappsActor, "type":"getAll"})["apps"]
      for app in apps:
        if app['name'] == app_manifest["name"]:
          if run:
            self.client.send({"to":webappsActor, "type":"launch", 'manifestURL': app['manifestURL']})

  def install(self, target_app_path):
    webappsActor = self.root["webappsActor"]

    zip_file = zip_path(target_app_path)
    app_file = open(zip_file, 'rb')
    data = app_file.read()
    file_size = len(data)

    upload_res = self.client.send({"to":webappsActor, "type":'uploadPackage', 'bulk': True})

    if 'actor' in upload_res and 'BulkActor' in upload_res['actor']:
      packageUploadActor = upload_res['actor']
      self.client.send_bulk(packageUploadActor, data)
    else: # Old B2G 1.4 and older, serialize binary data in JSON text strings (SLOW!)
      res = self.client.send({"to":webappsActor, "type":'uploadPackage'})
      packageUploadActor = upload_res['actor']
      chunk_size = 4*1024*1024
      i = 0
      while i < file_size:
        chunk = data[i:i+chunk_size]
        self.client.send_chunk(packageUploadActor, chunk)
        i += chunk_size

    app_local_id = str(uuid.uuid4())
    reply = self.client.send({"to":webappsActor, "type":'install', 'appId': app_local_id, 'upload': packageUploadActor})
    return reply['appId']

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
      # TODO Port should be a setting or autodiscover
      fp = Fireplay("localhost", 6080)

    self.tabs = [t for t in fp.get_tabs() if t['url'].find('about:') == -1]
    items = [t['url'] for t in self.tabs]
    self.view.window().show_quick_panel(items, self.selecting_tab)

  def selecting_tab(self, index):
    if index == -1: return
    fp.select_tab(self.tabs[index])

class FireplayStartFirefoxOsCommand(sublime_plugin.TextCommand):
  '''
  The Fireplay command for Firefox Os
  '''

  def run(self, edit):
    global fp

    if not fp:
      # TODO Port should be a setting or autodiscover
      fp = Fireplay("localhost", 62306)

    if not 'deviceActor' in fp.get_root():
      print "No device found"
      return

    folders = self.view.window().folders()
    self.manifests = list(filter(None, (get_manifest(f) for f in folders)))

    if not self.manifests:
      print "Nothing in here"
      return

    items = ["{0} - {1}".format(m[1]["name"], m[1]["description"]) for m in self.manifests]
    self.view.window().show_quick_panel(items, self.selecting_manifest)

  def selecting_manifest(self, index):
    if index == -1: return
    folder = self.manifests[index][0]
    fp.deploy(folder)

class FireplayStartCommand(sublime_plugin.TextCommand):
  '''
  The Fireplay main quick panel menu
  '''
  def run(self, editswi):
    mapping = {}
    
    # Let the user choose the device to connect
    # TODO eventually find possible connections available through ADB
    mapping['fireplay_start_firefox'] = 'Start Firefox with remote debug port 6080'
    mapping['fireplay_start_firefox_os'] = 'Start FirefoxOS with remote debug port 6080'
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

def zipdir(path, zipfilename):
  try:
    import zlib
    zip_mode = zipfile.ZIP_DEFLATED
  except:
    zip_mode = zipfile.ZIP_STORED

  zipf = zipfile.ZipFile(zipfilename, 'w', zip_mode)
  files_to_compress = []
  for root, dirs, files in os.walk(path):
    for file in files:
      files_to_compress += [(root, file)]

  n = 1
  for tuple in files_to_compress:
    (root, file) = tuple
    filename = os.path.join(root, file)
    filesize = os.path.getsize(filename)
    path_in_archive = os.path.relpath(filename, path)
    n += 1
    zipf.write(os.path.join(root, file), path_in_archive)
  zipf.close()

def get_manifest(target_app_path):
  if os.path.isdir(target_app_path):
    manifest_file = os.path.join(target_app_path, 'manifest.webapp')
    if not os.path.isfile(manifest_file):
      print "Error: Failed to find FFOS packaged app manifest file '" + manifest_file + "'! That directory does not contain a packaged app?"
      return None
    return (target_app_path, json.loads(open(manifest_file, 'r').read()))
  elif target_app_path.endswith('.zip') and os.path.isfile(target_app_path):
    try:
      z = zipfile.ZipFile(target_app_path, "r")
      bytes = z.read('manifest.webapp')
    except Exception, e:
      print "Error: Failed to read FFOS packaged app manifest file 'manifest.webapp' in zip file '" + target_app_path + "'! Error: " + str(e)
      return None
    return (target_app_path, json.loads(str(bytes)))
  else:
      print "Error: Path '" + target_app_path + "' is neither a directory or a .zip file to represent the location of a FFOS packaged app!"
      return None
  return None

def zip_path(target_app_path):
    (oshandle, tempzip) = tempfile.mkstemp(suffix='.zip', prefix='fireplay_temp_')
    zipdir(target_app_path, tempzip)

    # Remember to delete the temporary package after we quit.
    def delete_temp_file():
      os.remove(tempzip)

    atexit.register(delete_temp_file)
    return tempzip