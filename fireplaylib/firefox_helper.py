import mozrunner
import os
import sys
import subprocess

def start():
	DEFAULT_PREFS = {
	    # allow debug output via dump to be printed to the system console
	    # (setting it here just in case, even though PlainTextConsole also
	    # sets this preference)
	    'browser.dom.window.dump.enabled': True,
	    # warn about possibly incorrect code
	    'javascript.options.strict': True,
	    'javascript.options.showInConsole': True,

	    # Allow remote connections to the debugger
	    'devtools.debugger.remote-enabled' : True,

	    'extensions.sdk.console.logLevel': 'info',

	    'extensions.checkCompatibility.nightly' : False,

	    # Disable extension updates and notifications.
	    'extensions.update.enabled' : False,
	    'extensions.update.notifyUser' : False,

	    # From:
	    # http://hg.mozilla.org/mozilla-central/file/1dd81c324ac7/build/automation.py.in#l372
	    # Only load extensions from the application and user profile.
	    # AddonManager.SCOPE_PROFILE + AddonManager.SCOPE_APPLICATION
	    'extensions.enabledScopes' : 5,
	    # Disable metadata caching for installed add-ons by default
	    'extensions.getAddons.cache.enabled' : False,
	    # Disable intalling any distribution add-ons
	    'extensions.installDistroAddons' : False,
	    # Allow installing extensions dropped into the profile folder
	    'extensions.autoDisableScopes' : 10,

	    # Disable app update
	    'app.update.enabled' : False,

	    # Point update checks to a nonexistent local URL for fast failures.
	    'extensions.update.url' : 'http://localhost/extensions-dummy/updateURL',
	    'extensions.blocklist.url' : 'http://localhost/extensions-dummy/blocklistURL',
	    # Make sure opening about:addons won't hit the network.
	    'extensions.webservice.discoverURL' : 'http://localhost/extensions-dummy/discoveryURL',

	    'browser.startup.homepage' : 'about:blank',
	    'startup.homepage_welcome_url' : 'about:blank',
	    'devtools.errorconsole.enabled' : True,
	    'devtools.chrome.enabled' : True,
	    'devtools.debugger.remote-enabled' : True,
	    'devtools.debugger.remote-port': 6789,
	    'devtools.debugger.prompt-connection': False,

	    # From:
	    # http://hg.mozilla.org/mozilla-central/file/1dd81c324ac7/build/automation.py.in#l388
	    # Make url-classifier updates so rare that they won't affect tests.
	    'urlclassifier.updateinterval' : 172800,
	    # Point the url-classifier to a nonexistent local URL for fast failures.
	    'browser.safebrowsing.provider.0.gethashURL' : 'http://localhost/safebrowsing-dummy/gethash',
	    'browser.safebrowsing.provider.0.keyURL' : 'http://localhost/safebrowsing-dummy/newkey',
	    'browser.safebrowsing.provider.0.updateURL' : 'http://localhost/safebrowsing-dummy/update',
	}

	env = {}
	env.update(os.environ)
	env['MOZ_NO_REMOTE'] = '1'
	env['XPCOM_DEBUG_BREAK'] = 'stack'
	env['NS_TRACE_MALLOC_DISABLE_STACKS'] = '1'

	cmdargs = []
	if sys.platform == 'darwin':
	    cmdargs.append('-foreground')


	profile = mozrunner.FirefoxProfile(addons=[], preferences=DEFAULT_PREFS)
	runner = mozrunner.FirefoxRunner(
	    profile=profile,
	    env=env,
	    cmdargs=cmdargs,
	    kp_kwargs={
			"stdout":subprocess.PIPE,
	    	"stdin":subprocess.PIPE,
	    	"stderr":subprocess.PIPE
	    })

	runner.start()
