import os
import re
import psutil
import subprocess
import platform
SYSTEM = platform.system()

# Helper functions to locate the simulator

B2G_BIN_OSX = 'b2g/B2G.app/Contents/MacOS/b2g-bin'
FX_PROFILES_OSX = 'Library/Application Support/Firefox/Profiles/'

NETSTAT_CMD = 'netstat -lnptu'
LSOF_CMD = 'lsof -i -n -P -sTCP:LISTEN'


def is_simulator(extensions_path, extension):
    match = re.match('fxos_(.*)_simulator@mozilla.org$', extension)
    if not match:
        return False

    b2g_path = os.path.join(extensions_path, extension, B2G_BIN_OSX)
    return os.path.isfile(b2g_path)


def find_b2gs():
    if (SYSTEM == 'Darwin'):
        profiles_path = os.path.join(os.getenv('HOME'), FX_PROFILES_OSX)

    profiles = {}
    for profile in os.listdir(profiles_path):
        ext_path = os.path.join(profiles_path, profile, 'extensions')
        ext_dirs = os.listdir(ext_path)
        profiles[ext_path] = [
            ext
            for ext in ext_dirs
            if is_simulator(ext_path, ext)
        ]

    return profiles


def get_simulator_bin(ext_path, ext_b2g):
    if (SYSTEM == 'Darwin'):
        b2g_bin = B2G_BIN_OSX

    return os.path.join(ext_path, ext_b2g, b2g_bin)


def get_simulator_profile(ext_path, ext_b2g):
    return os.path.join(ext_path, ext_b2g, 'profile')


def run_simulator(ext_path, b2g_version):
    b2g_bin = get_simulator_bin(ext_path, b2g_version)
    b2g_profile = get_simulator_profile(ext_path, b2g_version)

    # TODO port has to change continuously
    B2G_COMMAND = '"{0}" -profile "{1}" -start-debugger-server 7654 -no-remote'

    b2g_command = B2G_COMMAND.format(b2g_bin, b2g_profile)
    return subprocess.Popen(
        b2g_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )

# Helper functions to find open simulators


def get_connections(p):
    try:
        return p.get_connections()
    except:
        return []


def is_listening(c):
    return c.status == 'LISTEN' and c.laddr[1] != 2828


def find_ports(p):
    return [c.laddr[1] for c in get_connections(p) if is_listening(c)]


def discover_rdp_ports():
    firefox = []
    firefoxos = []

    if SYSTEM == 'Darwin':
        output = os.popen(LSOF_CMD).read()
        for line in output.split('\n'):

            m = re.search('^(firefox|b2g)[-bin]?.*[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:([0-9]*)', line)
            if m:
                platform = m.group(1)
                port = int(m.group(2))

                if port == 2828:
                    continue

                if (platform == 'b2g'):
                    firefoxos.append(port)
                elif (platform == 'firefox'):
                    firefox.append(port)

    elif SYSTEM == 'Linux':
        output = os.popen(NETSTAT_CMD).read()
        for line in output.split('\n'):
            m = re.search('tcp.*[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:([0-9]*).*LISTEN.*/(firefox|b2g)', line)

            if m:
                platform = m.group(2)
                port = int(m.group(1))

                if port == 2828:
                    continue

                if (platform == 'b2g'):
                    firefoxos.append(port)
                elif (platform == 'firefox'):
                    firefox.append(port)
    else:

        for p in psutil.process_iter():
            name = p.name()
            if name == 'b2g-bin' or name == 'b2g':
                firefoxos = firefoxos + find_ports(p)
            elif name == 'firefox' or name == 'firefox-bin':
                firefox = firefox + find_ports(p)

    return {'firefox': firefox, 'firefoxos': firefoxos}

if __name__ == '__main__':
    print discover_rdp_ports()
