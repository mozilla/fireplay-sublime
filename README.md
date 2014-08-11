# Fireplay Sublime

> *ATTENTION:* this piece of code is super experimental and can be so radioactive that it could break your Sublime! It's going to be amazing.

The aim is to:

1. **Connect [Sublime Text](http://www.sublimetext.com/) to Firefox Developer tools**: live updating of HTML and CSS and reading the console logs directly from Sublime without any external tool, by using the **super-powerful** RDP (aka [Remote Debugging Protocol](https://wiki.mozilla.org/Remote_Debugging_Protocol)). This allows us to edit CSS at runtime exactly as if we were using the Web Inspector in Firefox.

2. **Use Sublime Text to deploy apps for FirefoxOS**: while the new [Firefox WebIDE](https://hacks.mozilla.org/2014/06/webide-lands-in-nightly/) is awesome, some developers might want to use their favourite editors.

## Installing (for the braves, on OS X and Linux)

```
$ cd ~/Library/Application\ Support/Sublime\ Text\ 2/Packages
$ git clone https://github.com/mozilla/fireplay-sublime fireplay
```

## Usage

Install the plugin by cloning into Sublime's plugin directory (as detailed above), then start Sublime Text.

#### Open a simulator
1. In Sublime Text, press `cmd`+`shift`+`r`.
2. If no simulator is open, select `Start new Firefox OS simulator instance`.

#### Start a connection
1. In Sublime Text, press `cmd`+`shift`+`r`.
2. Select the Firefox OS port and you are connected!

#### Push an app
1. Open the folder containing your Firefox OS app as a project in Sublime Text. This has to be the folder that contains the `manifest.webapp` file.
2. In Sublime Text, press `cmd`+`shift`+`r`.
3. A list of open apps will be shown. Select which one you want to deploy.

#### Push on save and live-reload css:
When you are connected to your device and pushed the app at least once, saving HTML and JS files will trigger a complete app push. Editing CSS files will only reload the CSS.

## Enable with Firefox Desktop (experimental)
Usage with Firefox is still experimental:

1. In Firefox `about:config` set `devtools.debugger.remote-enabled` to **true**
2. (optional) In Firefox `about:config` set `devtools.debugger.prompt-connection` to **false**
3. In your Sublime Text's packages folder, edit `fireplay.sublime-settings` and change
  ```
  fireplay_firefox: false,
  ```
  to
  ```
  fireplay_firefox: true,
  ```
4. In Firefox, open the Developer toolbar by going to `Tools`⟶ `Web Developer`⟶ `Developer toolbar`. A command line prompt will open at the bottom of the browser. Focus in it and type `listen`, then press `ENTER`.
5. You should now be able to live edit CSS and HTML from Sublime.

* * *

Read [INSPIRATIONS.md](INSPIRATIONS.md) to satisfy your unnatural curiosity.
