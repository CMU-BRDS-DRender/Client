#!/usr/bin/env python
from s3Utils import s3Client
from ec2Utils import ec2Client
import os
import sys
import json
import ast
import time
import urllib2,urllib
import requests
from shutil import rmtree
import argparse

class drenderProject():
	def __init__(self):

		# Variables for drenderProject
		self.localLog = 'drenderlogs.json'
		self.software = 'blender'
		self.startFrame = 1
		self.endFrame = 15
		self.fileName = 'demo2.03.blend'
		self.filePath = 'a.pdf'
		self.complete = False
		self.framesPerMachine = 50

	def setUpAWS(self):
		self.s3 = s3Client()
		self.ec2 = ec2Client()


		self.AWSAccessKey = ''
		self.AWSSecretKey = ''
		self.regionName = 'us-east-1a'


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
		self.s3.projectName = 'drender'

		# Variables for ec2
		self.ec2.instanceID = '' #Get from spawn
		self.ec2.instanceType = 't2.micro'
		self.ec2.AWSAmi = 'ami-065a51153f487ada4'

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
		parser = argparse.ArgumentParser()
		parser.add_argument("task",help="Select between start, end, download, status and running")
		parser.add_argument("--software",help="Select the type of file to be rendered. Only blender for now.")
		parser.add_argument("--path",help="Enter the path to the file to be rendered.")
		parser.add_argument("--startFrame",help="Enter the starting frame to be rendered.",type=int)
		parser.add_argument("--endFrame",help="Enter the ending frame to be rendered.",type=int)
		parser.add_argument("--framesPerMachine",help="Enter how many frames you want a single machine to render.(More frames = slower render,less cost).",type=int)
		parser.add_argument("--projectNumber",help="Enter the project number for end, download and status.")
		args = parser.parse_args()
		self.task = args.task
		if self.task == 'start':
			self.software = args.software
			self.filePath = args.path
			self.fileName = self.filePath.split('/')[-1]
			self.startFrame = args.startFrame
			self.endFrame = args.endFrame
			self.framesPerMachine = args.framesPerMachine
		elif self.task == 'end' or self.task == 'download' or self.task == 'status':
			self.projectName =  args.projectNumber
			
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
		if found == False:
			print "No such project exists.."
		return found

	def checkCurrentProjects(self):
		if not os.path.exists(self.localLog):
			print "File corrupted.."
		else:	
			with open(self.localLog,'r') as f:
				line = f.readline()
				noOfProjects = len(f.read())
				if(noOfProjects == 0):
					print "No Projects currently running.."
				else:
					print "Currently running projects are:"
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
		print "Your Project ID is:" + str(self.projectName)

	def getStatusUpdate(self):
		self.checkLocalLog()
		url = "http://" + self.ec2.publicDNSName + ":8080/status/" + self.projectName
		contents = urllib2.urlopen(url).read()
		data = json.loads(contents)
		self.s3.outputFiles = data['outputURI']['file']
		self.complete = data['complete']
		self.framesRendered = 0
		for job in data['log']['jobs']:
			self.framesRendered += job["framesRendered"]

	def sendDataToMaster(self):
		url = "http://" + self.ec2.publicDNSName + ":8080/start"
		bucketName = str(self.projectName) + "/" + str(self.fileName)
		data1 = {"id" : self.projectName, 
			"software": "blender",
			"source": {
				"bucketName": "drender",
				"file": bucketName},
			"startFrame": self.startFrame,
			"endFrame": self.endFrame,
			"publicIP":self.ec2.publicDNSName,
			"action": "START",
			"framesPerMachine":self.framesPerMachine}
		print "Starting Job Nodes.."
		r = requests.post(url,json=data1)
		print "Your Project is running.."


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
	percentage = (render1.framesRendered*10)/float(render1.endFrame)
	print "Project No. : " + render1.projectName;
	print "Status: " + str(percentage) + "% done"
elif render1.task == 'download':
	render1.setUpAWS()
	render1.s3.setUpS3()
	render1.getStatusUpdate()
	print render1.s3.outputFiles
	if(render1.complete == False):
		print "Project is not yet complete."
	else:
		print "Downloading rendered file"
		frames = render1.s3.downloadFileFromS3(render1.projectName)
		os.system("ffmpeg -r 20 -i temp/frame-%05d.jpg -b 9600 -qscale 5 drender_" + render1.fileName + ".mp4")
		rmtree("temp/")
elif render1.task == 'running':
	render1.checkCurrentProjects()
elif render1.task == 'end':
	print "End of project"
	render1.setUpAWS()
	render1.ec2.setUpEc2()
	render1.s3.setUpS3()
	if render1.checkLocalLog():
		render1.ec2.terminateInstance()
		render1.s3.deleteS3Bucket(render1.projectName)
		render1.deleteFromLog()
else:
	print "incorrect argument for task"


