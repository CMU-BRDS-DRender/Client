# Client
This is the client part of Drender. It is the interface for the user.

Run using "python drender.py"

It has 5 possible functions:
start, end, download, status and running.

start: This starts the actual program. It takes in extra arguments like the type of file, the path to the file, the start frame and the end frame.
end: This ends the project and all the dependancies in the cloud. It takes the Project ID as an argument.
download: This downloads the file after rendering and stitches them in one go. It takes the Project ID as an argument.
status: It gives the status of the rendering of the file in the cloud. It takes the Project ID as an argument.
runnning: This gives the currently running jobs.

Example Usage:
1. python drender.py start blender scene.blend 0 10 
2. python drender.py end 1
3. python drender.py download 1
4. python drender.py status 1
5. python drender.py running
