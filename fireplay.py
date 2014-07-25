import os
import sys
import sublime
import sublime_plugin
import re
import tempfile
import atexit
import zipfile
import uuid
import json

from fireplaylib.client import MozClient
reload(sys.modules['fireplaylib.client'])

fp = None
FIREPLAY_CSS = "CSSStyleSheet.prototype.reload = function reload(){\n    // Reload one stylesheet\n    // usage: document.styleSheets[0].reload()\n    // return: URI of stylesheet if it could be reloaded, overwise undefined\n    if (this.href) {\n        var href = this.href;\n        var i = href.indexOf('?'),\n                last_reload = 'last_reload=' + (new Date).getTime();\n        if (i < 0) {\n            href += '?' + last_reload;\n        } else if (href.indexOf('last_reload=', i) < 0) {\n            href += '&' + last_reload;\n        } else {\n            href = href.replace(/last_reload=\\d+/, last_reload);\n        }\n        return this.ownerNode.href = href;\n    }\n};\n\nStyleSheetList.prototype.reload = function reload(){\n    // Reload all stylesheets\n    // usage: document.styleSheets.reload()\n    for (var i=0; i<this.length; i++) {\n        this[i].reload()\n    }\n};"
FIREPLAY_CSS_RELOAD = "document.styleSheets.reload()"


class Fireplay:
    '''
    The Fireplay main client
    '''
    # TODO Blocking at the moment
    def __init__(self, host, port):
        self.client = MozClient(host, port)
        self.root = None
        self.selected_tab = None
        self.selected_app = None

    def get_root(self, force=False):
        if not self.root or force:
            self.root = self.client.send({
                'to': 'root',
                'type': 'listTabs'
            })

        return self.root

    def get_tabs(self, force=False):
        self.get_root(force)
        return self.root['tabs']

    # TODO allow multiple tabs with multiple codebase
    def select_tab(self, tab):
        self.selected_tab = tab

    def reload_css(self):
        console = self.selected_tab['consoleActor']

        # TODO Avoid touching prototype, shrink in one call only
        self.client.send({
            'to': console,
            'type': 'evaluateJS',
            'text': FIREPLAY_CSS,
            'frameActor': None
        })

        return self.client.send({
            'to': console,
            'type': 'evaluateJS',
            'text': FIREPLAY_CSS_RELOAD,
            'frameActor': None
        })

    def get_apps(self):
        return self.client.send({
            'to': self.root["webappsActor"],
            'type': 'getAll'
        })["apps"]

    def uninstall(self, manifestURL):
        self.client.send({
            'to': self.root["webappsActor"],
            'type': 'close',
            'manifestURL': manifestURL
        })
        self.client.send({
            'to': self.root["webappsActor"],
            'type': 'uninstall',
            'manifestURL': manifestURL
        })

    def launch(self, manifestURL):
        self.client.send({
            'to': self.root["webappsActor"],
            'type': 'launch',
            'manifestURL': manifestURL
        })

    def deploy(self, target_app_path, run=True, debug=False):
        app_manifest = get_manifest(target_app_path)[1]

        if run:
            for app in self.get_apps():
                if app['name'] == app_manifest['name']:
                    self.uninstall(app['manifestURL'])

        app_id = self.install(target_app_path)

        for app in self.get_apps():
            if app['id'] == app_id:
                self.selected_app = app
                self.selected_app['local_path'] = target_app_path

        if run:
            self.launch(self.selected_app['manifestURL'])

    def install(self, target_app_path):
        webappsActor = self.root['webappsActor']

        zip_file = zip_path(target_app_path)
        app_file = open(zip_file, 'rb')
        data = app_file.read()
        file_size = len(data)

        upload_res = self.client.send({
            'to': webappsActor,
            'type': 'uploadPackage',
            'bulk': True
        })

        if 'actor' in upload_res and 'BulkActor' in upload_res['actor']:
            packageUploadActor = upload_res['actor']
            self.client.send_bulk(packageUploadActor, data)
        else:
            # Old B2G 1.4 and older
            self.client.send({
                'to': webappsActor,
                'type': 'uploadPackage'
            })
            packageUploadActor = upload_res['actor']
            chunk_size = 4 * 1024 * 1024
            bytes = 0
            while bytes < file_size:
                chunk = data[bytes:bytes + chunk_size]
                self.client.send_chunk(packageUploadActor, chunk)
                bytes += chunk_size

        app_local_id = str(uuid.uuid4())
        reply = self.client.send({
            'to': webappsActor,
            'type': 'install',
            'appId': app_local_id,
            'upload': packageUploadActor
        })
        return reply['appId']

    def inject_css(self):

        webappsActor = self.root['webappsActor']
        res = self.client.send({
            'to': webappsActor,
            'type': 'getAppActor',
            'manifestURL': self.selected_app['manifestURL']
        })

        styleSheetsActor = res['actor']['styleSheetsActor']
        res = self.client.send({
            'to': styleSheetsActor,
            'type': 'getStyleSheets'
        })

        # TODO upload all css always? this should be a setting
        for styleSheet in res['styleSheets']:
            base_path = self.selected_app['local_path']
            manifest_path = self.selected_app['origin']
            css_path = styleSheet['href']
            css_file = base_path + css_path.replace(manifest_path, '')
            f = open(css_file, 'r')

            self.client.send({
                'to': styleSheet['actor'],
                'type': 'update',
                'text': f.read(),
                'transition': True
            })

            # TODO it is blocking. FXDEVTOOLS? new thread?
            self.client.receive()
            self.client.receive()
            self.client.receive()


class FireplayCssReloadOnSave(sublime_plugin.EventListener):
    '''
    Listener on save
    '''
    def on_post_save(self, view):
        global fp

        if not fp:
            return

        # TODO this should be a setting
        if not re.search(get_setting("reload_on_save_regex"), view.file_name()):
            return

        print fp.client.applicationType
        if fp.client.applicationType == 'browser':
            fp.reload_css()
        else:
            fp.inject_css()


class FireplayStartFirefoxCommand(sublime_plugin.TextCommand):
    '''
    The Fireplay command for Firefox Desktop
    '''
    def run(self, edit):
        global fp

        if not fp:
            # TODO Port should be a setting or autodiscover
            fp = Fireplay('localhost', int(get_setting('firefox_remote_port')))

        self.tabs = [t for t in fp.get_tabs() if t['url'].find('about:') == -1]
        items = [t['url'] for t in self.tabs]
        self.view.window().show_quick_panel(items, self.selecting_tab)

    def selecting_tab(self, index):
        if index == -1:
            return

        fp.select_tab(self.tabs[index])


class FireplayStartFirefoxOsCommand(sublime_plugin.TextCommand):
    '''
    The Fireplay command for Firefox Os
    '''

    def run(self, edit):
        global fp

        if not fp:
            # TODO Port should be a setting or autodiscover
            fp = Fireplay('localhost', int(get_setting('firefoxos_remote_port')))

        fp.get_root()

        folders = self.view.window().folders()
        self.manifests = list(filter(None, (get_manifest(f) for f in folders)))

        if not self.manifests:
            print 'Nothing in here'
            return

        items = [self.pretty_name(m) for m in self.manifests]
        self.view.window().show_quick_panel(items, self.selecting_manifest)

    def pretty_name(self, manifest):
        return '{0} - {1}'.format(manifest[1]['name'], manifest[1]['description'])

    def selecting_manifest(self, index):
        if index == -1:
            return

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
        if index == -1:
            return

        self.view.run_command(self.cmds[index])


def get_setting(key):
        s = sublime.load_settings('fireplay.sublime-settings')
        if s and s.has(key):
                return s.get(key)


def zipdir(path, zipfilename):
    try:
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
        # filesize = os.path.getsize(filename)
        path_in_archive = os.path.relpath(filename, path)
        n += 1
        zipf.write(os.path.join(root, file), path_in_archive)
    zipf.close()


def get_manifest(target_app_path):
    if os.path.isdir(target_app_path):
        manifest_file = os.path.join(target_app_path, 'manifest.webapp')
        if not os.path.isfile(manifest_file):
            print "Error: Failed to find FFOS packaged app manifest file '%s'! That directory does not contain a packaged app?" % manifest_file
            return None
        return (target_app_path, json.loads(open(manifest_file, 'r').read()))

    elif target_app_path.endswith('.zip') and os.path.isfile(target_app_path):
        try:
            z = zipfile.ZipFile(target_app_path, "r")
            bytes = z.read('manifest.webapp')
        except Exception, e:
            print "Error: Failed to read FFOS packaged app manifest file 'manifest.webapp' in zip file '%s'! Error: %s" % target_app_path, str(e)
            return None
        return (target_app_path, json.loads(str(bytes)))

    else:
        print "Error: Path '%s' is neither a directory or a .zip file to represent the location of a FFOS packaged app!" % target_app_path
        return None

    return None


def zip_path(target_app_path):
    (oshandle, tempzip) = tempfile.mkstemp(suffix='.zip', prefix='fireplay_')
    zipdir(target_app_path, tempzip)

    # Remember to delete the temporary package after we quit.
    def delete_temp_file():
        os.remove(tempzip)

    atexit.register(delete_temp_file)
    return tempzip
