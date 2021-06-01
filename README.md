# Web-based-Minecraft-server-control
### An web application made with Python, for peoples who wanted to control multiple Minecraft servers with just an URL.
## P.S Only Windows 10 is tested.
I don't see much peoples doing this via Python, less for Windows,
So here's the project which allows you to control your Minecraft Server online,
You can now easily control Minecraft Server using just a URL to login, send commands, view players or the terminal,
Whatever on PC or Mobile.

## How To Install:
#### 1. Install Python 3, Remember setup your environment for pip command
#### 2. Go inside `Setup` folder, run `setup.bat` for installing packages
#### 3. After this installing, back to the root folder.
#### 4. You can now open `main.py` to run this program
#### 5. When running, You can go to the control panel `http://localhost:7878` (port 7878 by default, you can change it in the `config.py` file)

## How To Use:
#### * Create a folder inside `Server`
#### * Put your Minecraft Server Core `xxx.jar` inside, name doesn't matter.
#### * If you had, put your `xxx.bat` inside as well, name doesn't matter. (P.S I recommand not having any PAUSE command inside your bat file, else the logger might acting strange.)
#### * Now, run and login to this program console(Default secret code is `admin`, HIGHLY RECOMMAND CHANGE IT IN THE `config.py` FIRST), you'll see the folder name.
#### * Start the server on the console allows you control on the browser.
#### * Enter commandline `stop` or use Ctrl+C to stop the program and close all remaining server at once.


After Your first run, Few files and folders will be generates.
## Original Files:
| Name | Type | Detail |
| --------------- | --------------- | --------------- |
| Setup | Folder | Contains all setup files for Installing necessary packages. |
| Src | Folder | Contains other required functions for `main.py` to be working. |
| templates | Folder | Contains all HTML files for HTTP access. |
| main.py | Python Executable | The entry point of this program. |
| config.py | Python Executable | The config of program |
## Extra Files After First Run:
| Name | Type | Detail |
| --------------- | --------------- | --------------- |
| Server | Folder | This is the folder where you can put lots of server inside, sparated by folder |
| Logs | Folder | Store all the logs |
| db.tinydb | Text File | Store some datas and settings |

All the remaining setting and configure information is inside the `config.py`,
You can change your port, binding IP from Internet or Localhost, secret code for login, or logs detail inside.
