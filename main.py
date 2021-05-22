from flask import Flask, request, render_template, url_for, session, redirect
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO, emit
from datetime import datetime
from tinydb import TinyDB, Query
from threading import Thread
import os, subprocess, waitress, time

Hosts = 1
IPs = ["0.0.0.0", "127.0.0.1"]
port = 7878
password = "rmh"
default_setup = "java -Xms1024m -Xmx1024m -XX:PermSize=128m -jar {0} nogui"
default_jarFile = "server.jar"

incoming = lambda req: logger("Incoming connection from {0}, target page {1}".format(req.remote_addr, req.path), 1)
PathExist = lambda path: os.path.exists(path)
genLog = lambda: str(datetime.now())[:-7].replace(" ", "_").replace(":","_") + ".log"

types = ["Info", "Warning", "Critical", "Success", "Failed"]
LoggerPath = "Logs/"
LogFile = genLog()

app = Flask(__name__, static_folder='templates/static', template_folder='templates')
CSRFProtect(app)
socketio = SocketIO(app)

Servers = {}

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

def reader(serverData):
    server = serverData[0]
    for i in iter(server.stdout.readline, ""):
        print(i)
        if i:
            buffer = i.decode("big5").strip()
            logger(buffer)
            socketio.emit("logs", {"log":buffer + "\n", "folder":serverData[1]})
        else:
            break
    del Servers[serverData[1]]
    socketio.emit("offline", {"folder": serverData[1]})

@app.route("/", methods=['GET', 'POST'])
def home():
    incoming(request)
    datas = request.form
    if datas.get("Admin"):
        if datas["Admin"] == password:
            session["secret"] = datas["Admin"]
    if session.get("secret") == password:
        return redirect(url_for("servers"))
    return render_template("index.html")
    
@app.route("/servers", methods=['GET'])
def servers():
    incoming(request)
    if session.get("secret") == password:
        folders = ""
        for f in [f for f in os.listdir("Server") if os.path.isdir(os.path.join("Server", f))]:
            folders += '<input type="submit" class="w3-button w3-block w3-red" style="width:100%; margin:0;" value="'+f+'" name="folder">'
        return render_template("servers.html", folders=("<div class='w3-red'><h4 style='margin:0'>No Server yet</h4></div>" if folders == "" else folders))
    return redirect(url_for("home"))
    
@app.route("/logout", methods=['GET'])
def logout():
    incoming(request)
    del session["secret"]
    return redirect(url_for("home"))
    
@socketio.on("cmd")
def command(data):
    folder = data.get("folder")
    cmd = data.get("cmd")
    folder = folder if folder in [f for f in os.listdir("Server") if os.path.isdir(os.path.join("Server", f))] else None
    if folder and cmd:
        server = Servers.get(folder)
        if server:
            server[0].stdin.write((cmd + "\n").encode("utf-8"))
            server[0].stdin.flush()

def readLog(loc):
    if os.path.exists(loc):
        with open(loc, "r") as file:
            return file.read()
    else:
        return ""
    
def getfiles(folder, ext, selected = None):
    pos = "setup" if ext == ".bat" else "jarFile"
    if os.path.exists(os.path.join("Server", folder)) and os.path.isdir(os.path.join("Server", folder)):
        files = [f for f in os.listdir("Server/" + folder) if f.endswith(ext)]
        if len(files) == 1:
            if selected != files[0]:
                db.update({pos:files[0]}, query.folder==folder)
            return "<option value='{0}' selected>{0}</option>".format(files[0])
        elif len(files) > 1:
            if selected == None:
                db.update({pos:files[0]}, query.folder==folder)
            return "".join([(("<option value='{0}'" + (" selected" if selected == f else "") + ">{0}</option>")).format(f) for f in os.listdir("Server/" + folder) if f.endswith(ext)])
    return "".join(["<option value='empty' disabled>No files.</option>"])
    
@app.route("/admin", methods=['GET', 'POST'])
def admin():
    incoming(request)
    datas = request.form
    if session.get("secret") == password:
        if request.method == "POST":
            folder = datas.get("folder")
            folder = folder if folder in [f for f in os.listdir("Server") if os.path.isdir(os.path.join("Server", f))] else None
            if folder:
                server = Servers.get(folder)
                log = readLog("Server/" + server[1] + "/logs/latest.log") if server else "Server not online yet"
                action = datas.get("action")
                if not db.get(query.folder == folder):
                    db.insert({"folder":folder, "setup":None, "jarFile":None})
                if datas.get("setup"):
                    db.update({"setup": datas.get("setup")}, query.folder==folder)
                if datas.get("jarfile"):
                    db.update({"jarFile": datas.get("jarfile")}, query.folder==folder)
                setupfile = db.get(query.folder == folder).get("setup")
                jarFile = db.get(query.folder == folder).get("jarFile")
                batlist = getfiles(folder, ".bat", setupfile)
                jarlist= getfiles(folder, ".jar", jarFile)
                setupfile = db.get(query.folder == folder).get("setup")
                jarFile = db.get(query.folder == folder).get("jarFile")
                if action and action.startswith("Turn "):
                    if server:
                        server[0].stdin.write(("stop\n").encode("utf-8"))
                        server[0].stdin.flush()
                        return render_template("admin.html", folder = folder, status = "on", log = "Server not online yet", jarlist= jarlist, batlist= batlist)
                    else:
                        if setupfile:
                            Servers[folder] = [subprocess.Popen(os.path.abspath("Server/" + folder + "/" + setupfile), stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, cwd = "Server/" + folder), folder, os.path.abspath("Server/" + folder + "/" + setupfile)]
                        elif jarFile:
                            Servers[folder] = [subprocess.Popen(default_setup.format(jarFile), stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, cwd = "Server/" + folder), folder, ""]
                        else:
                            return render_template("admin.html", folder = folder, status = "off", log = "", jarlist= jarlist, batlist= batlist)
                        read = Thread(target=reader, args=(Servers[folder], ))
                        read.setDaemon(True)
                        read.start()
                        return render_template("admin.html", folder = folder, status = "off", log = "", jarlist= jarlist, batlist= batlist)
                return render_template("admin.html", folder = folder, status = "off" if server else "on", log = log, jarlist= jarlist, batlist= batlist)
        return redirect(url_for("servers"))
    return redirect(url_for("home"))
    
    
db = TinyDB("db.tinydb")
query = Query()
print(db.all())

tmp = db.get(query.secret.exists())
if tmp: secret = tmp["secret"]
else:
    secret = str(os.urandom(24))
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
    except (KeyboardInterrupt, EOFError):
        serverStatus = False
    
logger("Shutdowning...")
for i in Servers.values():
    i[0].stdin.write(("stop\n").encode("utf-8"))
    i[0].stdin.flush()