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
		self.projectName = '1'
		self.URL = ''
		self.outputFiles = ''

	def setUpS3(self):
		sts_client = boto3.client('sts')
		assumedRoleObject = sts_client.assume_role(RoleArn="arn:aws:iam::214187139358:role/DRenderClientRole",RoleSessionName="UserSession1")
		credentials = assumedRoleObject['Credentials']
		self.s3 = boto3.resource('s3',
    aws_access_key_id = credentials['AccessKeyId'],
    aws_secret_access_key = credentials['SecretAccessKey'],
    aws_session_token = credentials['SessionToken'],
)
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
		files = self.bucket.objects.filter(Prefix=self.outputFiles)
		if not os.path.exists("temp/"):
			os.mkdir("temp/")
		for key in files:
			self.bucket.download_file(key.key,"temp/" + key.key[2:])
			frames.append("temp/" + key.key[2:])
		return frames

	def deleteS3Bucket(self,file):
		for obj in self.bucket.objects.filter(Prefix=str(file) +"/"):
			self.s3.Object(self.bucket.name, obj.key).delete()

