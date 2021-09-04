#!/usr/bin/python3
from flask import Flask, request, render_template, url_for, session, redirect
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO, emit
from flask_ipban import IpBan
from socketio import Client
from datetime import datetime
from tinydb import TinyDB, Query
from threading import Thread
from config import *
import matplotlib.pyplot as plt
import os, subprocess, time, psutil, platform, base64, io

incoming = lambda req: logger(Log_Incoming.format(req.remote_addr, req.path), 1)
PathExist = lambda path: os.path.exists(path)
genLog = lambda: str(datetime.now())[:-7].replace(" ", "_").replace(":","_") + ".log"

types = [Log_info, Log_warning, Log_critical, Log_success, Log_failed]

app = Flask(__name__, static_folder='templates/static', template_folder='templates')

db = TinyDB("db.tinydb")
query = Query()

tmp = db.get(query.secret.exists())
if tmp: secret = tmp["secret"]
else:
    secret = str(os.urandom(24))
    db.insert({"secret": secret})
    
app.config['SECRET_KEY'] = secret
CSRFProtect(app)
socketio = SocketIO(app)
ip_ban = IpBan(ban_seconds=BanSeconds, persist=PersistBan, ban_count=BanCount)
ip_ban.init_app(app)
ip_ban.load_allowed()
ip_ban.load_nuisances()
Servers = {}
rebootlist = []
LogFile = genLog()
encode = encode_nt if os.name == "nt" else encode_unix

def FolderInit(path):
    if not PathExist(path):
        os.makedirs(path)

def logger(msg, code = 0, show = True):
    #0 to 4 are available
    FolderInit(LoggerPath)
    with open(LoggerPath + LogFile, "a+", encoding=encode) as file:
        buffer = Log_format.format(types[code], datetime.now(), msg)
        if show: print(buffer)
        file.write(buffer + "\n")

def infoHTML():
    title, usage = [], []
    ram = psutil.virtual_memory()
    for i in Servers.values():
        title.append(i[1])
        usage.append(ramUsage(i[0].pid))
    if not Servers: title = ["Free"] ; usage = [1]
    f = plt.figure(figsize=(5,5))
    def func(pct, allvals):
        absolute = int(round(pct / 100 * sum(allvals)))
        return "{:.2f}%\n({:.2f} MB)".format(pct, absolute/1024**2)
    pie = plt.pie(usage, labels = title, autopct=lambda pct: func(pct, usage), colors=None if Servers else ["green"])
    for i in pie[2]: i.set_color("white")
    for i in pie[1]: i.set_color("white")
    plt.title("Server RAM Usage", color="white", fontsize="large", fontweight="bold")
    server = io.BytesIO()
    plt.savefig(server, format='png', transparent=True)
    server.seek(0)
    f.clear()
    plt.close()
    f = plt.figure(figsize=(5,5))
    data = [ram.available , ram.total - ram.available - sum(usage), sum(usage)]
    pie = plt.pie(data, labels=["Used", "Free", "Servers"], colors=["red", "green", "blue"], autopct=lambda pct: func(pct, data))
    for i in pie[2]: i.set_color("white")
    for i in pie[1]: i.set_color("white")
    plt.title("Total RAM Usage", color="white", fontsize="large", fontweight="bold")
    ramgraph = io.BytesIO()
    plt.savefig(ramgraph, format='png', transparent=True)
    ramgraph.seek(0)
    f.clear()
    plt.close()
    return """<div id="info"><ul><li>OS: {2}</li><li>Processor: {3}</li></ul></div><div id='graph'>
        <img id='Servers' src='data:image/png;base64, {0}'></img>
        <img id='Memory' src='data:image/png;base64, {1}'></img>
    </div>
    """.format(base64.b64encode(server.getvalue()).decode("utf-8"), \
    base64.b64encode(ramgraph.getvalue()).decode("utf-8"), platform.system() + " " + platform.release(), platform.machine())

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
    if session.get("secret") == password:
        if folder:
            if Servers.get(folder):
                if not folder in rebootlist:
                    rebootlist.append(folder)
                    logger("{0} scheduled a reboot for folder `{1}`.".format(request.remote_addr, folder), 1)
                Servers[folder][0].stdin.write(("stop\n").encode(encode))
                Servers[folder][0].stdin.flush()
        else:
            logger("{0} try to emit reboot without a folder.".format(request.remote_addr), 2)
            ip_ban.add()
    else:
        logger("{0} Used a wrong password to try emit reboot.".format(request.remote_addr), 2)
        ip_ban.add()

@app.route("/", methods=['GET', 'POST'])
def home():
    incoming(request)
    datas = request.form
    if datas.get("Admin"):
        if datas["Admin"] == password:
            session["secret"] = datas["Admin"]
        else:
            ip_ban.add()
            logger("{0} Failed to login with password `{1}`".format(request.remote_addr, datas.get("Admin")), 2)
    if session.get("secret") == password:
        return redirect(url_for("servers"))
    elif session.get("secret") != None:
        logger("{0} Have wrong password in session, it's `{1}`".format(request.remote_addr, session.get("secret")), 2)
        ip_ban.add()
        del session["secret"]
    return render_template("index.html")
    
@app.route("/servers", methods=['GET'])
def servers():
    incoming(request)
    if session.get("secret") == password:
        FolderInit(ServerPath)
        folders = ""
        for f in [f for f in os.listdir(ServerPath) if os.path.isdir(os.path.join(ServerPath, f))]:
            folders += '<input type="submit" class="w3-button w3-block ' + ("w3-green" if Servers.get(f) else "w3-red") + '" style="width:100%; margin:0;" value="'+f+'" name="folder">'
        return render_template("servers.html", folders=("<div class='w3-red'><h4 style='margin:0'>No Server yet</h4></div>" if folders == "" else folders), Info = infoHTML())
    logger("{0} Tried to use wrong password enter Servers, sending back to home.".format(request.remote_addr), 2)
    ip_ban.add()
    return redirect(url_for("home"))
    
@app.route("/logout", methods=['GET'])
def logout():
    incoming(request)
    try:
        del session["secret"]
    except Exception:
        "Never login before"
    logger("{0} Has been logout, sending back to home.".format(request.remote_addr), 1)
    return redirect(url_for("home"))
    
@socketio.on("forcestop")
def force(data):
    folder = data.get("folder")
    if session.get("secret") == password:
        if folder:
            if Servers.get(folder):
                kill_child(Servers[folder][0].pid)
                logger("{0} killed the folder `{1}`".format(request.remote_addr, folder), 1)
            else:
                logger("{0} tried to force stop a server not even online or exist. `{1}`".format(request.remote_addr, folder), 1)
        else:
            logger("{0} tried to emit forcestop without telling which folder.".format(request.remote_addr), 2)
            ip_ban.add()
    else:
        logger("{0} Used a wrong password to try emit force stop.".format(request.remote_addr), 2)
        ip_ban.add()

@socketio.on("cmd")
def command(data):
    folder = data.get("folder")
    cmd = data.get("cmd")
    folder = folder if folder in [f for f in os.listdir(ServerPath) if os.path.isdir(os.path.join(ServerPath, f))] else None
    if session.get("secret") == password:
        if folder and cmd:
            server = Servers.get(folder)
            if server:
                logger("{0} Send command to `{1}`, The commandline is `{2}`".format(request.remote_addr, folder, cmd), 1)
                server[0].stdin.write((cmd + "\n").encode(encode_unix))
                server[0].stdin.flush()
            elif cmd == "stop":
                setupfile = db.get(query.folder == folder).get("setup")
                jarFile = db.get(query.folder == folder).get("jarFile")
                if jarFile:
                    if setupfile:
                        Servers[folder] = [subprocess.Popen(os.path.abspath(ServerPath + folder + "/" + setupfile) if os.name == "nt" else ["sh", os.path.abspath(ServerPath + folder + "/" + setupfile)], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, cwd = ServerPath + folder, shell=False), folder, os.path.abspath(ServerPath + folder + "/" + setupfile)]
                    else:
                        Servers[folder] = [subprocess.Popen(default_setup.format(jarFile).split(), stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, cwd = ServerPath + folder, shell=False), folder, ""]
                    emit("online", {"folder": folder}, broadcast=True)
                    read = Thread(target=reader, args=(Servers[folder], ))
                    read.setDaemon(True)
                    read.start()
                    logger("{0} boot the folder `{1}`".format(request.remote_addr, folder), 1)
                else:
                    logger("{0} Failed to boot server, .jar file doesn't exist in the Server folder.".format(request.remote_addr, folder, cmd), 2)
        else:
            if folder == None: 
                logger("{0} Tried to enter a folder not exist! `{1}`".format(request.remote_addr, folder), 2)
                ip_ban.add()
            else:
                logger("{0} Tried to send empty command to the folder `{1}`".format(request.remote_addr, folder), 2)
    else:
        logger("{0} Used a wrong password to try emit cmd.".format(request.remote_addr), 2)
        ip_ban.add()
        
def readLog(loc):
    if os.path.exists(loc):
        with open(loc, "rb") as file:
            return file.read().decode(encode_nt, errors="ignore")
    return ""
        
def kill_child(pid):    
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    for child in children:
        child.kill()
    gone, still_alive = psutil.wait_procs(children, timeout=5)
    
def ramUsage(pid):
    ram = psutil.Process(pid).memory_info().rss
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    for child in children: ram += psutil.Process(child.pid).memory_info().rss
    return ram

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
            return "".join([(("<option value='{0}'" + (" selected" if selected == f else "") + ">{0}</option>")).format(f) for f in files])
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
                log = readLog(ServerPath + server[1] + "/logs/latest.log") if server else ""
                action = datas.get("action")
                if not db.get(query.folder == folder):
                    db.insert({"folder": folder, "setup": None, "jarFile": None, "autoreboot": "disable"})
                    logger("{0} Initialized folder {1}.".format(request.remote_addr, folder), 1)
                if datas.get("setup"):
                    db.update({"setup": datas.get("setup")}, query.folder==folder)
                    logger("{0} Updated {1}'s setup config, changed to {2}.".format(request.remote_addr, folder, datas.get("setup")), 1)
                if datas.get("jarfile"):
                    db.update({"jarFile": datas.get("jarfile")}, query.folder==folder)
                    logger("{0} Updated {1}'s jarfile config, changed to {2}.".format(request.remote_addr, folder, datas.get("jarfile")), 1)
                if datas.get("autoreboot"):
                    db.update({"autoreboot": datas.get("autoreboot")}, query.folder==folder)
                    logger("{0} Updated {1}'s autoreboot config, changed to {2}.".format(request.remote_addr, folder, datas.get("autoreboot")), 1)
                setupfile = db.get(query.folder == folder).get("setup")
                jarFile = db.get(query.folder == folder).get("jarFile")
                autoreboot = db.get(query.folder == folder).get("autoreboot")
                execlist = getfiles(folder, "setup", setupfile)
                jarlist= getfiles(folder, "jarFile", jarFile)
                setupfile = db.get(query.folder == folder).get("setup")
                jarFile = db.get(query.folder == folder).get("jarFile")
                logger("{0} Accessed folder `{1}`".format(request.remote_addr, folder), 1)
                return render_template("admin.html", folder = folder, status = "off" if server else "on", log = log, jarlist= jarlist, execlist= execlist, titleColor = "w3-green" if server else "w3-red", statustag = "online" if server else "offline", ar_e = "selected" if autoreboot == "enable" else "", ar_d = "selected" if autoreboot == "disable" else "")
        logger("{0} seems not selecting Server before enter Admin, sending to view server list.".format(request.remote_addr), 2)
        ip_ban.add()
        return redirect(url_for("servers"))
    logger("{0} Tried wrong login info, sending back to Home.".format(request.remote_addr), 2)
    ip_ban.add()
    return redirect(url_for("home"))
    
FolderInit(ServerPath)
webpanel = Thread(target=socketio.run, args=(app, ), kwargs={"host":IPs[Hosts], "port":port})
webpanel.setDaemon(True)
webpanel.start()

logger(Log_start)
serverStatus = True
while serverStatus:
    try:
        cmd = input()
        logger(cmd, show=False)
        cmd = cmd.lower()
        if cmd == "stop":
            serverStatus = False
        elif cmd.startswith("ban "):
            data = cmd.split()
            if len(data) > 1:
                ip_ban.block(data[1], permanent=True)
                logger("IP {0} banned for permanent.`".format(data[1]), 3)
            else:
                logger("Required Format: `ban %IP_Address%`", 4)
        elif cmd.startswith("unban "):
            data = cmd.split()
            if len(data) > 1:
                ip_ban.remove(data[1])
                logger("IP {0} has been unbanned.`".format(data[1]), 3)
            else:
                logger("Required Format: `unban %IP_Address%`", 4)
        elif cmd == "banlist":
            if ip_ban.get_block_list():
                for k, r in ip_ban.get_block_list().items():
                    logger(" * {0}, Warn: {1}, Forver: {2}, When: {3}".format(k, r['count'], r.get('permanent', ''), r['timestamp']), 3)
            else:
                logger("Blacklist is empty.", 3)
        elif cmd == "help":
            logger(" - Command Help -", 3)
            logger("ban %IP_Address% - Ban an IP Address permanently.", 3)
            logger("unban %IP_Address% - UnBan an IP Address.", 3)
            logger("banlist - Show the banned IP Address list.", 3)
            logger("help - Show this Command Help.", 3)
            logger("stop - Stop this program.", 3)
            logger(" - End - ", 3)
            
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
