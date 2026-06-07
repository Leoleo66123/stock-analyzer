# launcher.py - PyInstaller entry
import sys, os, time, webbrowser, subprocess, socket, logging

PORT = 8501
log_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(
    filename=os.path.join(log_dir, 'stock_startup.log'),
    level=logging.INFO,
    format='%(asctime)s %(message)s'
)

def get_root():
    return sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

ROOT = get_root()

def find_free_port(start=8501):
    for p in range(start, start + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', p)) != 0:
                return p
    return start

def is_streamlit_child():
    """检测是否是 Streamlit 内部 spawn 的子进程（如 script runner）"""
    argv = sys.argv
    for a in argv:
        if 'streamlit' in a.lower():
            return True
    if 'STREAMLIT_SERVER_RUN_ON_SAVE' in os.environ:
        return True
    return False

def run_streamlit_directly():
    """透传模式：Streamlit 子进程直接跑服务，不做 launcher 逻辑"""
    port = PORT
    for i, a in enumerate(sys.argv):
        if a == '--server.port' and i + 1 < len(sys.argv):
            try: port = int(sys.argv[i+1])
            except: pass
    os.chdir(ROOT)
    sys.path.insert(0, ROOT)
    sys.path.insert(0, os.path.join(ROOT, 'modules'))
    import streamlit.web.bootstrap
    streamlit.web.bootstrap.run(
        os.path.join(ROOT, 'app.py'),
        is_hello=False, args=[], flag_options={}
    )

def main():
    # 如果是 Streamlit 内部 spawn 的子进程，直接透传
    if is_streamlit_child():
        logging.info('Streamlit child process, running directly')
        run_streamlit_directly()
        return

    frozen = getattr(sys, 'frozen', False)
    logging.info(f'Frozen={frozen}')

    # 主流程：启动 worker 子进程，打开浏览器
    port = find_free_port(PORT)
    url = f'http://localhost:{port}'
    logging.info(f'Target: {url}')

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0

    # 子进程用 worker.py 跑 streamlit（比透传更干净）
    proc = subprocess.Popen(
        [sys.executable, os.path.join(ROOT, 'worker.py'), str(port)],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    logging.info(f'Worker PID={proc.pid}')

    import urllib.request
    for i in range(120):
        if proc.poll() is not None:
            logging.error(f'Worker exited code={proc.returncode}')
            return
        try:
            urllib.request.urlopen(urllib.request.Request(url), timeout=2)
            logging.info(f'Ready: {url}')
            webbrowser.open(url)
            break
        except Exception:
            time.sleep(1)
    else:
        logging.error('Timeout')

    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()

if __name__ == '__main__':
    main()