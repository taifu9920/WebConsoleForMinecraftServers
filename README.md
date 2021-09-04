# Web Console For Minecraft Servers
### An web application made with Python, design to maintenance more than one server, via HTML. 
## Now tested on Windows 10, Ubuntu 20.04 LTS.
I don't see much peoples doing this with Python, and most for Linux not Windows.
So I tried to make this project that allows control for all Minecraft servers with an URL.
This can be used to send commands to specific server, reboot, and view online players(WIP).
Whatever on PC or Mobile.

## How To Install
# For Windows 10:
#### 1. Install Python 3 from https://www.python.org/, Remember setup your environment for pip command.
#### 2. Clone this repo via git bash or download and unzip it.
#### 3. Go inside `Setup` folder, run `setup.bat` to install required packages.
#### 4. After this installing, back to the root folder.
#### 5. You can now open `main.py` to run this program.

# For Ubuntu 20.04 LTS or any Linux OS
#### 1. Install Python 3 via command `sudo apt install python3 python3-pip`.
#### 2. Clone this repo via command `git clone https://github.com/taifu9920/Web-based-Minecraft-server-control`.
#### 3. Use `cd Web-based-Minecraft-server-control/Setup`, then `chmod +x setup.sh`, `./setup.sh`.
#### 4. After installing required packages, use `cd ..` to get back the parent folder.
#### 5. Use `chmod +x main.py`, then you can now use `./main.py` to run this program.

## How To Use:
#### 1. Create a folder inside `Servers`, eg: `test`, it'll be `Servers/test`.
#### 2. Put your Minecraft Server Core `xxx.jar` inside the folder you created, name doesn't matter, eg: `Servers/test/server.jar`.
#### 3. If you had, put your `.sh` or `.bat` executable file inside as well, name doesn't matter, eg: `Servers/test/start.sh` or `Servers/test/start.bat`.
#### 4. Now, run this program, and open your browser, enter the URL `http://localhost:7878`. (Default port is 7878, you can change it in the file `config.py`)
#### 5. The default secret code is `admin`, after login you'll see the folder name. (HIGHLY RECOMMAND CHANGE THE SECRET CODE INSIDE `config.py` FIRST)
#### 6. Now you should be able to control the server you just setup on the browser.
#### 7. Enter the command `stop` to stop the program and close all remaining server one by one.
#### 8. For more commands please enter `help` to view.

After Your first run, Few files and folders will be generates.
## Original Files:
| Name | Type | Detail |
| --------------- | --------------- | --------------- |
| Setup | Folder | Contains all setup files for Installing necessary packages. |
| templates | Folder | Contains all HTML files for HTTP access. |
| ip_ban | Folder | Setting file for ip_ban module |
| main.py | Python Executable | The entry point of this program. |
| config.py | Python Executable | The config of program |
## Extra Files After First Run:
| Name | Type | Detail |
| --------------- | --------------- | --------------- |
| Servers | Folder | This is the folder where you can put lots of server inside, sparated by folder |
| Logs | Folder | Store all the logs |
| db.tinydb | Text File | Store some datas and settings |

All the remaining setting and configure information is inside the `config.py`,
You can change your port, binding IP from Internet or Localhost, secret code for login, or logs detail inside.

# Incomplete:
### * 200ms buffer load for logs.
### * ~~A better HTML interface with designs~~
### * ~~Page for changing config file~~
### * Page for viewing past logs
### * View all plugins
### * View online players
### * Plugin Installion on HTML interface
### * ~~More information like RAM~~, server runtime, etc.
