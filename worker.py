# worker.py - runs streamlit server (called by launcher)
import sys, os
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8501

ROOT = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'modules'))

# Set the real sys.argv so streamlit child spawns work correctly
sys.argv = [
    'streamlit', 'run', os.path.join(ROOT, 'app.py'),
    '--server.port', str(PORT),
    '--server.headless', 'true',
    '--server.runOnSave', 'false',
    '--browser.gatherUsageStats', 'false',
    '--server.enableCORS', 'false',
    '--server.enableXsrfProtection', 'false',
    '--logger.level', 'error',
    '--global.developmentMode', 'false',
]

import streamlit.web.bootstrap
streamlit.web.bootstrap.run(
    os.path.join(ROOT, 'app.py'),
    is_hello=False, args=[], flag_options={}
)