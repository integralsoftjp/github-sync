#!/usr/bin/python3
from wsgiref.simple_server import make_server
import subprocess
import json
import threading
import logging
import os
import yaml


homepath = os.environ["HOME"]
with open(f'config.yaml') as file:
  config = yaml.safe_load(file.read())

sth = logging.StreamHandler()
flh = logging.FileHandler('http.log')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO, handlers=[sth, flh])
logger = logging.getLogger(__name__)

def git_clone(giturl):
  cmd = f'git -C {homepath}/ clone {giturl}'
  result = subprocess.run(cmd, shell=True, encoding='utf-8', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  if result.returncode == 0:
    logger.info(f'clone[{result.returncode}] {homepath} stdout: {result.stdout.strip()}')
  else:
    logger.error(f'clone[{result.returncode}] {homepath} stderr: {result.stderr.strip()}')

def git_pull(dir):
  cmd = f'git -C {dir} pull'
  result = subprocess.run(cmd, shell=True, encoding='utf-8', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  if result.returncode == 0:
    logger.info(f'pull[{result.returncode}] {dir} stdout: {result.stdout.strip()}')
  else:
    logger.error(f'pull[{result.returncode}] {dir} stderr: {result.stderr.strip()}')

def deploy():  # deploy用
  for result in config['service']:
    dir_name = f'{homepath}/{result["dir"]}'
    gitremoteurl = result["remoteurl"]
    dir_exists = os.path.exists(dir_name)
    if dir_exists:
      git_pull(dir_name)
    else:
      git_clone(gitremoteurl)

def webhook_app(environ, start_response):
  print("gitpull done!")
  status = '200 OK'
  headers = [
    ('Content-type', 'application/json; charset=utf-8'),
    ('Access-Control-Allow-Origin', '*'),
  ]

  start_response(status, headers)

  method = environ.get('REQUEST_METHOD')
  # contentの長さを取得する
  content_length = environ.get('CONTENT_LENGTH', 0)
  if content_length == '':
    content_length = '0'
  # 指定した長さの分だけファイルオブジェクトをreadする
  if method == 'POST' and content_length != '0':
      body = environ.get('wsgi.input').read(int(content_length))
      # body_text = body.decode(encoding='utf-8')
      body_text = json.loads(body)
      body_text_ref = body_text['ref'].split('/').pop()
      if (body_text_ref == 'master') or (body_text_ref == 'main'):
          # レスポンスが遅れてしまうのでスレッドを分ける
          deploy_thread = threading.Thread(target=deploy)
          deploy_thread.start()

  return [json.dumps({}).encode("utf-8")]

def main():
  httpd = make_server('', 20000, webhook_app)
  print("Serving on port 20000...")
  httpd.serve_forever()

if __name__ == "__main__":
  main()