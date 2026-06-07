# run.py - Launcher: finds Python, starts Streamlit, opens browser
import subprocess, sys, os, time, webbrowser, socket, logging

PORT = 8501
EXE_DIR = os.path.dirname(os.path.abspath(sys.executable))

logging.basicConfig(
    filename=os.path.join(EXE_DIR, 'startup.log'),
    level=logging.INFO,
    format='%(asctime)s %(message)s'
)

def find_python():
    for path in [
        os.path.join(os.environ.get('LOCALAPPDATA',''), 'Python', 'pythoncore-3.14-64', 'python.exe'),
        os.path.join(os.environ.get('LOCALAPPDATA',''), 'Python', 'pythoncore-3.13-64', 'python.exe'),
        os.path.join(os.environ.get('LOCALAPPDATA',''), 'Python', 'pythoncore-3.12-64', 'python.exe'),
        os.path.join(os.environ.get('ProgramFiles',''), 'Python312', 'python.exe'),
        os.path.join(os.environ.get('ProgramFiles',''), 'Python313', 'python.exe'),
        'python.exe',
    ]:
        if os.path.exists(path):
            return path
    return 'python.exe'

def find_free_port(start=8501):
    for p in range(start, start+50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1',p)) != 0:
                return p
    return start

def main():
    logging.info(f'EXE_DIR={EXE_DIR}')
    python = find_python()
    port = find_free_port(PORT)
    url = f'http://localhost:{port}'
    app = os.path.join(EXE_DIR, 'app.py')
    logging.info(f'Python={python} exists={os.path.exists(python)}')
    logging.info(f'App={app} exists={os.path.exists(app)}')

    if not os.path.exists(app):
        logging.error('app.py not found!')
        return

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0

    proc = subprocess.Popen(
        [python, '-m', 'streamlit', 'run', app,
         '--server.port', str(port),
         '--server.headless', 'true',
         '--browser.gatherUsageStats', 'false',
         '--server.enableCORS', 'false',
         '--server.enableXsrfProtection', 'false',
         '--logger.level', 'error'],
        cwd=EXE_DIR,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    logging.info(f'Streamlit PID={proc.pid}')

    import urllib.request
    for i in range(120):
        if proc.poll() is not None:
            logging.error(f'Streamlit died code={proc.returncode}')
            return
        try:
            urllib.request.urlopen(urllib.request.Request(url), timeout=2)
            logging.info(f'Ready: {url}')
            webbrowser.open(url)
            break
        except: time.sleep(1)
    else:
        logging.error('Timeout')
    proc.wait()

if __name__ == '__main__':
    main()