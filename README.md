# Client
This is the client part of Drender. It is the interface for the user.

Run using "python drender.py"

It has 5 possible functions:
start, end, download, status and running.

Tasks: 
1. start: starts the drender service to render the required scenes.
    Arguments: software, path, startframe, endframe, framespermachine
2. end: ends the drender service. 
    Arguments: projectnumber
3. download: Downloads and stitches the rendered frames.
    Argument: projectnumber
4. status: Gets the status of the jobs from the service.
    Arguments: projectnumber
5. running: Gets locally saved information about currently running projects.
    Arguments: None
6. help: Shows usage information and other client related stuff.

usage: drender.py [-h] [--software SOFTWARE] [--path PATH]
                  [--startFrame STARTFRAME] [--endFrame ENDFRAME]
                  [--framesPerMachine FRAMESPERMACHINE]
                  [--projectNumber PROJECTNUMBER]
                  task

positional arguments:
  task                  Select between start, end, download, status and
                        running

optional arguments:
  -h, --help            show this help message and exit

  --software SOFTWARE   Select the type of file to be rendered. Only blender for now.

  --path PATH           Enter the path to the file to be rendered.

  --startFrame STARTFRAME Enter the starting frame to be rendered.

  --endFrame ENDFRAME   Enter the ending frame to be rendered.

  --framesPerMachine FRAMESPERMACHINE Enter how many frames you want a single machine to render.(More frames = slower render,less cost).

  --projectNumber PROJECTNUMBER Enter the project number for end download and status.

Example Usage:
1. python drender.py start --software blender --path scene.blend --startFrame 0 --endFrame 10 --framesPerMachine 20
2. python drender.py end --projectNumber 1
3. python drender.py download --projectNumber 1
4. python drender.py status --projectNumber 1
5. python drender.py running
6. python drender.py --help
