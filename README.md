# Web-based-Minecraft-server-control
### An web application made with Python, for peoples who wanted to control multiple Minecraft servers with just an URL.
I don't see much peoples doing this via Python, less for Windows,
So here's the project which allows you to control your Minecraft Server online,
You can now easily control Minecraft Server using just a URL to login, send commands, view players or the terminal,
Whatever on PC or Mobile.

## How To Install:
#### 1. Install Python 3, And this only support Windows 10 for now
 * (I only tested **Windows 10** for this, Not sure if **Windows xp, 7 or 8** or other supports too.) 
#### 2. Go inside `Setup` folder, run `setup.bat`
#### 3. After this installing, back to the root folder.
#### 4. You can now open `main.py` to run this program
#### 5. When running, You can go to the control panel `http://localhost:7878` (port 7878 by default, you can change it in the `main.py` file)

After Your first run, Few files and folders will be generates.
## Original Files:
| Name | Type | Detail |
| --------------- | --------------- | --------------- |
| Setup | Folder | Contains all setup files for Installing necessary packages. |
| Src | Folder | Contains other required functions for `main.py` to be working. |
| templates | Folder | Contains all HTML files for HTTP access. |
| Main.py | Python Executable | The entry point of this program. |  
## Extra Files After First Run:
| Name | Type | Detail |
| --------------- | --------------- | --------------- |
| Server | Folder | This is the folder where you can put lots of server inside, sparated by folder |
| Logs | Folder | Store all the logs |
| db.tinydb | Text File | Store some datas and settings |
