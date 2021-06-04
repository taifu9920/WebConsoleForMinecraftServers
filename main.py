#!/usr/bin/python3
from flask import Flask, request, render_template, url_for, session, redirect
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO, emit
from socketio import Client
from datetime import datetime
from tinydb import TinyDB, Query
from threading import Thread
from config import *
import os, subprocess, time, psutil

incoming = lambda req: logger(Log_Incoming.format(req.remote_addr, req.path), 1)
PathExist = lambda path: os.path.exists(path)
genLog = lambda: str(datetime.now())[:-7].replace(" ", "_").replace(":","_") + ".log"

types = [Log_info, Log_warning, Log_critical, Log_success, Log_failed]

app = Flask(__name__, static_folder='templates/static', template_folder='templates')
CSRFProtect(app)
socketio = SocketIO(app)
Servers = {}
rebootlist = []
LogFile = genLog()
encode = encode_nt if os.name == "nt" else encode_unix

def FolderInit(path):
    if not PathExist(path):
        os.makedirs(path)

def logger(msg, code = 0):
    #0 to 4 are available
    FolderInit(LoggerPath)
    with open(LoggerPath + LogFile, "a+", encoding=encode) as file:
        buffer = Log_format.format(types[code], datetime.now(), msg)
        print(buffer)
        file.write(buffer + "\n")

def reader(serverData):
    sio = Client()
    sio.connect("http://localhost:" + str(port), namespaces=["/"])
    while True:
        server = serverData[0]
        folder = serverData[1]
        for i in iter(server.stdout.readline, ""):
            if i:
                buffer = i.decode(encode).strip()
                if (LogOnConsole): logger(buffer)
                sio.emit("side", {"log":buffer + "\n", "folder":folder, "verify":str(app.config['SECRET_KEY'])})
            else:
                break
        del Servers[folder]
        sio.emit("side", {"folder": folder, "state":"offline", "verify":str(app.config['SECRET_KEY'])})
        if serverStatus and (db.get(query.folder == folder).get("autoreboot") == "enable" or folder in rebootlist):
            if folder in rebootlist: rebootlist.remove(folder)
            setupfile = db.get(query.folder == folder).get("setup")
            jarFile = db.get(query.folder == folder).get("jarFile")
            if setupfile:
                serverData = [subprocess.Popen(os.path.abspath(ServerPath + folder + "/" + setupfile) if os.name == "nt" else ["sh", os.path.abspath(ServerPath + folder + "/" + setupfile)], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, cwd = ServerPath + folder, shell=False), folder, os.path.abspath(ServerPath + folder + "/" + setupfile)]
            elif jarFile:
                serverData = [subprocess.Popen(default_setup.format(jarFile).split(), stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, cwd = ServerPath + folder, shell=False), folder, ""]
            else:
                return
            Servers[folder] = serverData
            sio.emit("side", {"folder": folder, "state":"online", "verify":str(app.config['SECRET_KEY'])})
        else:
            return

@socketio.on("side")
def secretDatas(data):
    if (str(app.config['SECRET_KEY']) == data.get("verify")):
        if(data.get("log")):
            emit("logs", {"log": data.get("log"), "folder": data.get("folder")}, broadcast=True)
        elif(data.get("state")):
            emit(data.get("state"), {"folder": data.get("folder")}, broadcast=True)

@socketio.on("reboot")
def reboot(data):
    folder = data.get("folder")
    if folder:
        if Servers.get(folder):
            if not folder in rebootlist:
                rebootlist.append(folder)
            Servers[folder][0].stdin.write(("stop\n").encode(encode))
            Servers[folder][0].stdin.flush()

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
        FolderInit(ServerPath)
        folders = ""
        for f in [f for f in os.listdir(ServerPath) if os.path.isdir(os.path.join(ServerPath, f))]:
            folders += '<input type="submit" class="w3-button w3-block ' + ("w3-green" if Servers.get(f) else "w3-red") + '" style="width:100%; margin:0;" value="'+f+'" name="folder">'
        return render_template("servers.html", folders=("<div class='w3-red'><h4 style='margin:0'>No Server yet</h4></div>" if folders == "" else folders))
    return redirect(url_for("home"))
    
@app.route("/logout", methods=['GET'])
def logout():
    incoming(request)
    del session["secret"]
    return redirect(url_for("home"))
    
@socketio.on("forcestop")
def force(data):
    folder = data.get("folder")
    if folder:
        if Servers.get(folder):
            kill_child(Servers[folder][0].pid)

@socketio.on("cmd")
def command(data):
    folder = data.get("folder")
    cmd = data.get("cmd")
    folder = folder if folder in [f for f in os.listdir(ServerPath) if os.path.isdir(os.path.join(ServerPath, f))] else None
    if folder and cmd:
        server = Servers.get(folder)
        if server:
            server[0].stdin.write((cmd + "\n").encode(encode))
            server[0].stdin.flush()
        elif cmd == "stop":
            setupfile = db.get(query.folder == folder).get("setup")
            jarFile = db.get(query.folder == folder).get("jarFile")
            if setupfile:
                Servers[folder] = [subprocess.Popen(os.path.abspath(ServerPath + folder + "/" + setupfile) if os.name == "nt" else ["sh", os.path.abspath(ServerPath + folder + "/" + setupfile)], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, cwd = ServerPath + folder, shell=False), folder, os.path.abspath(ServerPath + folder + "/" + setupfile)]
            elif jarFile:
                Servers[folder] = [subprocess.Popen(default_setup.format(jarFile).split(), stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, cwd = ServerPath + folder, shell=False), folder, ""]
            else:
                return "ERROR"
            emit("online", {"folder": folder}, broadcast=True)
            read = Thread(target=reader, args=(Servers[folder], ))
            read.setDaemon(True)
            read.start()

def readLog(loc):
    if os.path.exists(loc):
        with open(loc, "r", encoding=encode) as file:
            return file.read()
    return ""
        
def kill_child(pid):    
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    for child in children:
        child.kill()
    gone, still_alive = psutil.wait_procs(children, timeout=5)
    
def getfiles(folder, pos, selected = None):
    if os.path.exists(os.path.join(ServerPath, folder)) and os.path.isdir(os.path.join(ServerPath, folder)):
        files = [f for f in os.listdir(ServerPath + folder) if (f.endswith(".jar") if pos == "jarFile" else (f.endswith(".bat") or f.endswith(".sh")))]
        if len(files) == 1:
            if selected != files[0]:
                db.update({pos:files[0]}, query.folder==folder)
            return "<option value='{0}' selected>{0}</option>".format(files[0])
        elif len(files) > 1:
            if selected == None:
                db.update({pos:files[0]}, query.folder==folder)
            return "".join([(("<option value='{0}'" + (" selected" if selected == f else "") + ">{0}</option>")).format(f) for f in os.listdir("Server/" + folder) if f.endswith(ext)])
        db.update({pos:None}, query.folder==folder)
    return "".join(["<option value='empty' disabled>No files.</option>"])
    
@app.route("/admin", methods=['GET', 'POST'])
def admin():
    incoming(request)
    datas = request.form
    if session.get("secret") == password:
        if request.method == "POST":
            folder = datas.get("folder")
            folder = folder if folder in [f for f in os.listdir(ServerPath) if os.path.isdir(os.path.join(ServerPath, f))] else None
            if folder:
                server = Servers.get(folder)
                log = readLog(ServerPath + server[1] + "/logs/latest.log") if server else "Server not online yet"
                action = datas.get("action")
                if not db.get(query.folder == folder):
                    db.insert({"folder":folder, "setup":None, "jarFile":None, "autoreboot":"disable"})
                if datas.get("setup"):
                    db.update({"setup": datas.get("setup")}, query.folder==folder)
                if datas.get("jarfile"):
                    db.update({"jarFile": datas.get("jarfile")}, query.folder==folder)
                if datas.get("autoreboot"):
                    db.update({"autoreboot": datas.get("autoreboot")}, query.folder==folder)
                setupfile = db.get(query.folder == folder).get("setup")
                jarFile = db.get(query.folder == folder).get("jarFile")
                autoreboot = db.get(query.folder == folder).get("autoreboot")
                execlist = getfiles(folder, "setup", setupfile)
                jarlist= getfiles(folder, "jarFile", jarFile)
                setupfile = db.get(query.folder == folder).get("setup")
                jarFile = db.get(query.folder == folder).get("jarFile")
                return render_template("admin.html", folder = folder, status = "off" if server else "on", log = log, jarlist= jarlist, execlist= execlist, titleColor = "w3-green" if server else "w3-red", statustag = "online" if server else "offline", ar_e = "selected" if autoreboot == "enable" else "", ar_d = "selected" if autoreboot == "disable" else "")
        return redirect(url_for("servers"))
    return redirect(url_for("home"))
    
db = TinyDB("db.tinydb")
query = Query()

tmp = db.get(query.secret.exists())
if tmp: secret = tmp["secret"]
else:
    secret = str(os.urandom(24))
    db.insert({"secret": secret})
    
app.config['SECRET_KEY'] = secret
FolderInit(ServerPath)
webpanel = Thread(target=socketio.run, args=(app, ), kwargs={"host":IPs[Hosts], "port":port})
webpanel.setDaemon(True)
webpanel.start()

logger(Log_start)
serverStatus = True
while serverStatus:
    try:
        cmd = input().lower()
        if cmd == "stop":
            serverStatus = False
    except (KeyboardInterrupt, EOFError):
        serverStatus = False
    
logger(Log_stop)
for i in list(Servers.values()):
    i[0].stdin.write(("y\nstop\n").encode(encode))
    i[0].stdin.flush()
    
for i in list(Servers.values()):
    logger(Log_wait.format(i[1]))
    while i in Servers.values():
        time.sleep(1)
