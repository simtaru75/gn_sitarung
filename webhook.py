from flask import Flask
import subprocess

app = Flask(__name__)

@app.route('/deploy', methods=['POST'])
def deploy():
    subprocess.Popen(
        ['/home/geonode/geonode-project/deploy.sh'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)