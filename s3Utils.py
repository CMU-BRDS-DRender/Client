import boto3
from botocore.exceptions import ClientError
import os

class s3Client():
	def __init__(self):
		self.AWSAccessKey = ''
		self.AWSSecretKey = ''
		self.regionName = ''
		self.fileName = ''
		self.bucketExists = False
		self.filePath = ''
		self.projectName = 'jobname3'
		self.URL = ''

	def setUpS3(self):
		#print "Creating bucket: " + self.projectName
		session = boto3.Session(profile_name='default')
		self.s3 = session.resource('s3')
		self.bucket = self.s3.Bucket(self.projectName)
		try:
			self.s3.meta.client.head_bucket(Bucket=self.projectName)
			self.bucketExists = True
		except ClientError as e:
			self.s3.create_bucket(Bucket=self.projectName, CreateBucketConfiguration={'LocationConstraint':self.regionName})
			self.bucketExists = False

	def checkS3Health(self):
		try:
			self.s3.meta.client.head_bucket(Bucket=self.projectName)
			self.bucketExists = True
			print "S3 bucket exists.."
		except ClientError as e:
			self.s3.create_bucket(Bucket=self.projectName, CreateBucketConfiguration={'LocationConstraint':self.regionName})
			self.bucketExists = False
			print "S3 bucket does not exist.."

	def createBucket(self):	
		#print "Creating bucket: " + str(self.projectName)
		try:
			self.s3.meta.client.head_bucket(Bucket=self.projectName)
			self.bucket = self.s3.Bucket(self.projectName)
		except ClientError as e:
			self.s3.create_bucket(Bucket=self.projectName, CreateBucketConfiguration={'LocationConstraint':self.regionName})
			self.bucket = self.s3.Bucket(self.projectName)

	def uploadFileToS3(self,file):
		print "Uploading your file.."
		self.s3.Object(self.projectName, str(file) +"/" + self.fileName).put(Body=open(self.filePath, 'rb'),ACL='public-read')
		self.URL = "https://s3-" + self.regionName + ".amazonaws.com/" + self.projectName + "/" + self.fileName

	def downloadFileFromS3(self,file):
		frames = list()
		files = self.bucket.objects.filter(Prefix=str(file) + "/")
		if not os.path.exists("temp/"):
			os.mkdir("temp/")
		for key in files:
			self.bucket.download_file(key.key,"temp/" + key.key[2:])
			frames.append("temp/" + key.key[2:])
		return frames

	def deleteS3Bucket(self,file):
		for obj in self.bucket.objects.filter(Prefix=str(file) +"/"):
			self.s3.Object(self.bucket.name, obj.key).delete()

