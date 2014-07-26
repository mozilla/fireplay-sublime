import os
import re
import psutil

# Helper functions to locate the simulator

B2G_BIN_MAC = 'b2g/B2G.app/Contents/MacOS/b2g-bin'
FX_PROFILES_MAC = 'Library/Application Support/Firefox/Profiles/'


def is_simulator(extensions_path, extension):
    match = re.match('fxos_(.*)_simulator@mozilla.org$', extension)
    if not match:
        return False

    b2g_path = os.path.join(extensions_path, extension, B2G_BIN_MAC)
    return os.path.isfile(b2g_path)


def find_b2gs():
    profiles = {}

    profiles_path = os.path.join(os.getenv('HOME'), FX_PROFILES_MAC)
    for profile in os.listdir(profiles_path):
        ext_path = os.path.join(profiles_path, profile, 'extensions')
        ext_dirs = os.listdir(ext_path)
        profiles[ext_path] = [ext for ext in ext_dirs if is_simulator(ext_path, ext)]

    return profiles

# Helper functions to find open simulators


def get_connections(p):
    try:
        return p.get_connections()
    except:
        return []


def is_listening(c):
    return c.status == "LISTEN" and c.laddr[1] != 2828


def find_ports(p):
    return [c.laddr[1] for c in get_connections(p) if is_listening(c)]


def discover_rdp_ports():
    firefox = []
    firefoxos = []
    for p in psutil.process_iter():
        name = p.name()
        if name == 'b2g-bin' or name == 'b2g':
            firefoxos = firefoxos + find_ports(p)
        elif name == 'firefox' or name == 'firefox-bin':
            firefox = firefox + find_ports(p)

    return {'firefox': firefox, 'firefoxos': firefoxos}

if __name__ == '__main__':
    print discover_rdp_ports()
    print find_b2gs()
