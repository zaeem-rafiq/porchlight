"""Start standalone Next.js server for Porchlight Console."""
import os
import subprocess
import sys
import time
from dotenv import load_dotenv

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()
sys.path.insert(0, REPO_ROOT)
from scripts.deploy_apprunner import get_anon_key

url = os.environ.get("SUPABASE_URL", "").rstrip("/")
anon = get_anon_key()
env = {
    **os.environ,
    "PORT": "3000",
    "HOSTNAME": "0.0.0.0",
    "NEXT_PUBLIC_SUPABASE_URL": url,
    "NEXT_PUBLIC_SUPABASE_ANON_KEY": anon,
    "SUPABASE_URL": url,
    "SUPABASE_ANON_KEY": anon,
}
standalone_dir = os.path.join(REPO_ROOT, "console", ".next", "standalone")
p = subprocess.Popen(["node", "server.js"], cwd=standalone_dir, env=env)
p.wait()
