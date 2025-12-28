from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'https://t.me/roxybasicneedbot1'


if __name__ == "__main__":
    app.run()
