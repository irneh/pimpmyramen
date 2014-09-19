import boto
import flask as f
import flask.ext.uploads as fu
import os
import redis
import time
import urlparse
import uuid

app = f.Flask(__name__)
app.debug = os.getenv('APP_DEBUG')

## Redis.
url = urlparse.urlparse(os.environ.get('REDISCLOUD_URL'))
r = redis.Redis(host=url.hostname, port=url.port, password=url.password)

## Flask-Uploads config.
app.config['UPLOADED_IMAGES_DEST'] = 'tmp'
images = fu.UploadSet('images', ('gif', 'bmp', 'png', 'jpg', 'jpeg'))
fu.configure_uploads(app, (images))

## S3.
S3_BUCKET = os.getenv('S3_BUCKET')
c = boto.connect_s3()
b = c.get_bucket(S3_BUCKET)
k = boto.s3.key.Key(b)

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
