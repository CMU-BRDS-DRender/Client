from s3Utils import s3Client
from ec2Utils import ec2Client
import os
import sys
import json
import ast
import time
import urllib2,urllib

class drenderProject():
	def __init__(self):

		# Variables for drenderProjecy
		self.localLog = 'drenderlogs.json'
		self.software = 'blender'
		self.startFrame = 0
		self.endFrame = 10
		self.fileName = 'render_file.blend'
		self.filePath = 'a.pdf'

	def setUpAWS(self):
		self.s3 = s3Client()
		self.ec2 = ec2Client()


		self.AWSAccessKey = ''
		self.AWSSecretKey = ''
		self.regionName = 'us-west-2'


		# Variables for s3 and ec2
		self.s3.AWSAccessKey = self.AWSAccessKey
		self.ec2.AWSAccessKey = self.AWSAccessKey
		self.s3.AWSSecretKey = self.AWSSecretKey
		self.ec2.AWSSecretKey = self.AWSSecretKey
		self.s3.regionName = self.regionName
		self.ec2.regionName = self.regionName
		self.s3.fileName = self.fileName
		self.ec2.fileName = self.fileName
		self.ec2.filePath = self.filePath
		self.s3.filePath = self.filePath

		# Variables for s3
		self.s3.bucketExists = False
		self.s3.projectName = 'jobname3'

		# Variables for ec2
		self.ec2.instanceID = '' #Get from spawn
		self.ec2.instanceType = 't2.micro'
		self.ec2.AWSAmi = 'ami-0bbe6b35405ecebdb'

	def checkProjectExists(self):
		if os.path.exists(self.localLog):	
			f = open(self.localLog,'r')
			text = f.read()
			f.close()
			if self.s3.projectName in text:
				return True
			else:
				return False
		else:
			return False

	def getCommandLineArguments(self):
		self.task = sys.argv[1]
		if self.task == 'start':
			self.software = sys.argv[2]
			self.filePath = sys.argv[3]
			self.fileName = self.filePath.split('/')[-1]
			self.startFrame = sys.argv[4]
			self.endFrame = sys.argv[5]
		elif self.task == 'end' or self.task == 'download' or self.task == 'status':
			self.projectName =  str(sys.argv[2])
			
	def initializeLog(self):
		logEntry = {
		"id":"000",
		"software":"Blender",
		"S3Source":"S3URL",
		"MasterNodeIP":"IP",
		"InstanceID":"InstanceID",
		"startFrame":"StartFrame#",
		"endFrame":"endFrame#"
		}
		with open(self.localLog,'w+') as file:
			file.write(str(logEntry))
			file.write('\n')

	def updateLog(self):
		if not os.path.exists(self.localLog):
			self.initializeLog()

		data = dict()
		lastID = 0
		with open(self.localLog,'r') as f:
			line = f.readline()
			while line:
				#print line
				data = ast.literal_eval(line[:])
				lastID = data['id']
				line = f.readline()
		self.projectName = int(lastID) + 1

		logEntry = {
		"id":self.projectName,
		"software":self.software,
		"S3Source":self.s3.URL,
		"MasterNodeIP":self.ec2.publicDNSName,
		"InstanceID":self.ec2.instanceID,
		"startFrame":self.startFrame,
		"endFrame":self.endFrame
		}

		with open(self.localLog,'a') as f:
			f.write(str(logEntry))
			f.write('\n')

	def checkLocalLog(self):
		found = False
		if not os.path.exists(self.localLog):
			print "File corrupted.."
		else:	
			with open(self.localLog,'r') as f:
				line = f.readline()
				while line:
					data = ast.literal_eval(line[:])
					if int(self.projectName) == int(data['id']):
						found = True
						print "Found project: " + self.projectName
						self.ec2.publicDNSName = data['MasterNodeIP']
						self.ec2.instanceID = data['InstanceID']
						break
					line = f.readline()
		if found:
			print "No such project exists.."
		return found

	def checkCurrentProjects(self):
		if not os.path.exists(self.localLog):
			print "File corrupted.."
		else:	
			with open(self.localLog,'r') as f:
				line = f.readline()
				while line:
					data = ast.literal_eval(line[:])
					if(int(data['id']) != 0):
						print "Project ID: " + str(data['id'])
					line = f.readline()


	def startProject(self):
		self.s3.createBucket()
		self.ec2.spawnNewMaster()
		self.updateLog()
		self.s3.uploadFileToS3(self.projectName)
		print "Your job ID is:" + str(self.projectName)

	def getStatusUpdate(self):
		self.checkLocalLog()
		url = self.ec2.publicDNSName + "/status"
		contents = urllib2.urlopen(url).read()
		print contents

	def sendDataToMaster(self):
		url = self.ec2.publicDNSName + "/start"
		bucketName = str(self.projectName) + "/" + str(self.fileName)
		data = urllib.urlencode({'id' : self.projectName, "software": "blender","source": {"bucketName": "drender","file": bucketName},"startFrame": self.startFrame,"endFrame": self.endFrame,"action": "START"})
		req = urllib2.Request(url, data)
		response = urllib2.urlopen(req)
		d = response.read()
		print d

	def deleteFromLog(self):
		bad_words = [self.projectName]
		with open(self.localLog) as oldfile, open('temp.json', 'w+') as newfile:
		    for line in oldfile:
		        if not any(bad_word in line for bad_word in bad_words):
		            newfile.write(line)
		os.rename("temp.json",self.localLog)


render1 = drenderProject()
render1.getCommandLineArguments()

if render1.task == 'start':
	print "Initializing Drender.."
	render1.setUpAWS()
	render1.ec2.setUpEc2()
	render1.s3.setUpS3()
	render1.startProject()
	render1.sendDataToMaster()
elif render1.task == 'status':
	print "Fetching Status"
	render1.setUpAWS()
	render1.ec2.setUpEc2()
	render1.getStatusUpdate()
elif render1.task == 'download':
	print "Downloading rendered file"
	render1.setUpAWS()
	render1.s3.setUpS3()
	frames = render1.s3.downloadFileFromS3(render1.projectName)
	print frames
	print os.system("ffmpeg -qscale 5 -r 20 -b 9600 -i img%05d.png drender_" + render1.fileName + ".mp4")
elif render1.task == 'running':
	print "Currently running projects are:"
	render1.checkCurrentProjects()
elif render1.task == 'end':
	print "End of project"
	render1.setUpAWS()
	render1.ec2.setUpEc2()
	render1.s3.setUpS3()
	render1.checkLocalLog()
	render1.ec2.terminateInstance()
	render1.s3.deleteS3Bucket(render1.projectName)
	render1.deleteFromLog()
else:
	print "incorrect argument for task"




"""
	python drender.py start blender a.pdf 0 10 
	TO DO:
	1. Get ffmpeg info from file instead of user/static
"""

		
