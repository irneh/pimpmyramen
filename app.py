import flask as f
import os
import redis
import time
import urlparse

url = urlparse.urlparse(os.environ.get('REDISCLOUD_URL'))
r = redis.Redis(host=url.hostname, port=url.port, password=url.password)

app = f.Flask(__name__)
app.debug = os.getenv('APP_DEBUG')

@app.route('/', methods=['GET'])
def index():
  return f.render_template('index.html')

@app.route('/api', methods=['GET', 'POST'])
def api():
  t = r.get('t')
  t = time.asctime(time.gmtime(float(t)))
  return t

@app.route('/set', methods=['GET', 'POST'])
def set():
  r.set('t', time.time())
  return(f.redirect(f.url_for('index')))

if __name__ == '__main__':
  app.run()
