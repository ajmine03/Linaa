from tools.ffuf import build_command as build_ffuf
from tools.httpx import build_command as build_httpx
from tools.nmap import build_command as build_nmap
from tools.nuclei import build_command as build_nuclei
from tools.whatweb import build_command as build_whatweb


TOOL_BUILDERS = {
    "nmap": build_nmap,
    "httpx": build_httpx,
    "whatweb": build_whatweb,
    "nuclei": build_nuclei,
    "ffuf": build_ffuf,
}