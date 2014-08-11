# Fireplay Sublime

> *ATTENTION:* this piece of code is super experimental and can be so radioactive that it could break your Sublime! It's going to be amazing.

The aim is to:

1. **Connect [Sublime Text](http://www.sublimetext.com/) to Firefox Developer tools**: live-updates of HTML and CSS, read console logs can be done directly from Sublime without any external tool by connecting to **super-powerful** RDP (aka [Remote Debugging Protocol](https://wiki.mozilla.org/Remote_Debugging_Protocol)). This allow us to edit CSS during runtime exactly as the Web Inspector would.

2. **Use Sublime Text to deploy apps for FirefoxOS**: while the new [Firefox WebIDE](https://hacks.mozilla.org/2014/06/webide-lands-in-nightly/) is awesome, some developers might want to use their favourite editors.

## Installing (for braves on OS X and Linux)

```
$ cd ~/Library/Application\ Support/Sublime\ Text\ 2/Packages
$ git clone https://github.com/mozilla/fireplay-sublime fireplay
```

## Usage

Usage instruction are even more experimental and will be soon simplified.

#### Open a simulator
1. In Sublime Text, press `cmd`+`shift`+`r`
2. If no simulator is open, select "Start new FirefoxOS instance"

#### Start a connection
1. In Sublime Text, press `cmd`+`shift`+`r`
2. Select the FirefoxOS port and you are connected!

#### Push an app
1. Open the folder containing your manifest.webapp in Sublime Text.
2. In Sublime Text, press `cmd`+`shift`+`r`
3. A list of opened apps is shown, select the one to deploy

#### Push on save and live-reload css:
Once you are connected to your device and pushed the app, saving html and js files will cause a push, editing css files will reload the css only

## Enable with Firefox Desktop (experimental)
Usage with Firefox is still experimental:

1. In Firefox `about:config` set `devtools.debugger.remote-enabled` to **true**
2. (optional) In Firefox `about:config` set `devtools.debugger.prompt-connection` to **false**
3. In your Sublime Text's packages folder, change in fireplay.sublime-settings
  ```
  fireplay_firefox: false,
  ```
  to
  ```
  fireplay_firefox: true,
  ```
4. Open the `Tools`->`Web Developer` ->`Developer toolbar` and type `listen`

* * *

Read [INSPIRATIONS.md](INSPIRATIONS.md) to satisfy your innatural curiosity.
