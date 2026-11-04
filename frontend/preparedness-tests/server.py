"""Real synthetic FastAPI and production static build on an isolated test port."""
import sys
from pathlib import Path
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from backend.synthetic_api import create_synthetic_app
app=create_synthetic_app()
worker_revision = 0

@app.post('/__test__/worker/{revision}')
def change_worker(revision: int):
    global worker_revision
    worker_revision = revision
    return {'revision': revision}

@app.get('/preparedness/service-worker.js')
def worker():
    text = (ROOT/'frontend/dist/preparedness/service-worker.js').read_text()
    if worker_revision:
        text = text.replace('const CACHE = "gridguide-preparedness-', f'const CACHE = "gridguide-preparedness-test{worker_revision}-')
    return Response(text, media_type='text/javascript', headers={'Cache-Control': 'no-store'})

app.mount('/',StaticFiles(directory=ROOT/'frontend/dist',html=True),name='production-static')
if __name__=='__main__':
    uvicorn.run(app,host='127.0.0.1',port=18186,log_level='warning',access_log=False)
