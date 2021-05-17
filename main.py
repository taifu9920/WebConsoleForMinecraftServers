from flask import Flask, request, render_template, url_for
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
from tinydb import TinyDB, Query
from threading import Thread
import os, subprocess, waitress

Hosts = 0
IPs = ["0.0.0.0", "127.0.0.1"]
port = 7878

types = ["Info", "Warning", "Critical", "Success", "Failed"]
LoggerPath = "Logs/"
LogFile = str(datetime.now())[:-7].replace(" ", "_").replace(":","_") + ".log"

app = Flask(__name__, static_folder='templates/static', template_folder='templates')
CSRFProtect(app)

incoming = lambda req: logger("Incoming connection from {0}, target page {1}".format(req.remote_addr, req.path), 1)
PathExist = lambda path: os.path.exists(path)

server = []

def FolderInit(path):
    if not PathExist(path):
        os.makedirs(path)

def logger(msg, code = 0):
    #0 to 4 are available
    FolderInit(LoggerPath)
    with open(LoggerPath + LogFile, "a+", encoding='UTF-8') as file:
        buffer = "{0} | {1} : {2}".format(types[code], datetime.now(), msg)
        print(buffer)
        file.write(buffer + "\n")

def reader(server):
    for i in iter(server.stdout.readline, ""):
        if i:
            logger(i.rstrip().decode("utf-8"))
        else:
            break

@app.route("/", methods=['GET', 'POST'])
def home():
    incoming(request)
    if request.method == "POST":
        datas = request.form
        if datas.get("cmd"):
            if len(server) > 0:
                server[0].stdin.write((datas["cmd"] + "\n").encode("utf-8"))
                server[0].stdin.flush()
                return "OK"
        elif datas.get("action"):
            if datas["action"] == "start":
                if len(server) == 0:
                    server.append(subprocess.Popen("java -Xms1024m -Xmx1024m -XX:PermSize=128m -jar server.jar nogui", stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, cwd = "Server"))
                    read = Thread(target=reader, args=(server[0],))
                    read.setDaemon(True)
                    read.start()
                    return "Server Started"
        return "Failed"
    else:
        return render_template("index.html")
    
    
db = TinyDB("db.tinydb")
query = Query()

tmp = db.get(query.secret.exists())
if tmp: secret = tmp["secret"]
else:
    secret = str(urandom(24))
    db.insert({"secret": secret})
    
app.config['SECRET_KEY'] = secret
webpanel = Thread(target=waitress.serve, args=(app, ), kwargs={"host":IPs[Hosts], "port":port})
webpanel.setDaemon(True)
webpanel.start()

logger("Server is running now!\nUse Ctrl + 'c' to stop.")
serverStatus = True
while serverStatus:
    try:
        cmd = input().lower()
        if cmd == "stop":
            serverStatus = False
    except KeyboardInterrupt:
        serverStatus = False
    
logger("Shutdowning...")
if len(server) > 0:
    server[0].stdin.write(("stop\n").encode("utf-8"))