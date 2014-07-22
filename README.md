# Fireplay Sublime

This is a thing that connects to WebIDE and does cool things. It's going to be amazing.
*ATTENTION:* this piece of code is super experimental and can be so radio-active that could break your Sublime!

## Aim
The aim to:

1. **Connect editor to Firefox Developer tools**
Live-updates of HTML and CSS, read console logs can be done directly from Sublime without any external tool by connecting to **super-powerful** RDP (aka [Remote Debugging Protocol](https://wiki.mozilla.org/Remote_Debugging_Protocol)). This allow us to edit CSS during runtime exactly as the Web Inspector would.

2. **Use the editor to deploy apps for FirefoxOS**
While the new [Firefox WebIDE](https://hacks.mozilla.org/2014/06/webide-lands-in-nightly/) is awesome! Some developers might want to use their favourite editors.

## Installing (for braves on OS X)

1. Install the plugin
```
$ cd ~/Library/Application Support/Sublime Text 2/Packages
$ git clone https://github.com/mozilla/fireplay-sublime fireplay
```
2. In Firefox `about:config` set `devtools.debugger.remote-enabled` to **true**

## Usage

Usage instruction are even more experimental and will be soon simplified.

### Usage (long way but safer)

1. Open browser and `shift`+`F2` and type `listen`
2. Run `cmd`+`shift`+`p`
3. In Sublime select `Fireplay` and follow the instruction

### Usage (short way but less safe)

1. In Firefox `about:config` set `devtools.debugger.prompt-connection` to **false**

## Inspirations
### Existing projects and libraries to explore

* https://github.com/campd/python-fxdevtools
* https://github.com/harthur/firefox-client

#### Change UI in real time
* [Paul's implementation of live-css with devtools](https://github.com/paulrouget/firefox-remote-styleEditors/blob/master/libs/fxui.py)

#### Deploy from command line

* [Offer a command line tool that communicates with the device and webapps actor](https://bugzilla.mozilla.org/show_bug.cgi?id=1023084)
* [CLI app tools should have a way to push apps](https://bugzilla.mozilla.org/show_bug.cgi?id=1035185#c1)
* [Emscripten ffdb.py for b2g interaction](https://github.com/kripken/emscripten/blob/master/tools/ffdb.py)
* [WebIDE implementation for pushing the app in javascript](http://mxr.mozilla.org/mozilla-central/source/toolkit/devtools/apps/app-actor-front.js)

## Ideas

* Remote style editor (start there, probably performance issues, gotta work around that)
* Binding Sublime console
