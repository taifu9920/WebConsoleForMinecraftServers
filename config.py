#-----Connection Setting-----
Hosts = 0 # 0 for Internet, 1 for Localhost
port = 7878 # Change this to change the connect port
password = "admin" # VERY RECOMMAND CHANGE THIS DEFAULT PASSWORD TO ANYTHING ELSE
#----------------------------
#-----Other Setting-----
LogOnConsole = False # Change this to decide showing all server logs on program console or not
LoggerPath = "Logs/"
ServerPath = "Servers/"
BanCount = 11
BanSeconds = 43200
PersistBan = True
#----------------------------






#DO NOT CHANGE BELOW UNLESS YOU KNOW WHAT YOU'RE DOING
#-----Logging Configure-----
Log_info = "Info"
Log_warning = "Warning"
Log_critical = "Critical"
Log_success = "Success"
Log_failed = "Failed"

Log_Incoming = "Incoming connection from {0}, target page {1}"
Log_format = "{0} | {1} : {2}"
Log_start = "Server is running now!\nEnter 'stop' to stop."
Log_stop = "Shutdowning..."
Log_wait = "Waiting for Server `{0}` to close"
#---------------------------
#-----Other Setting-----
encode_nt = "big5"
encode_unix = "utf-8"
IPs = ["0.0.0.0", "127.0.0.1"]
default_setup = "java -Xms1024m -Xmx1024m -XX:PermSize=128m -jar {0} nogui"
default_jarFile = "server.jar"
#----------------------------
