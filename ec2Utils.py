import boto3
from botocore.exceptions import ClientError
import time

class ec2Client():
	def __init__(self):	
		self.AWSAccessKey = ''
		self.AWSSecretKey = ''
		self.regionName = ''
		self.instanceID = ''
		self.fileName = ''
		self.instanceType = ''
		self.filePath = ''
		self.AWSAmi = ''

	def setUpEc2(self):
		sts_client = boto3.client('sts')
		assumedRoleObject = sts_client.assume_role(RoleArn="arn:aws:iam::214187139358:role/DRenderClientRole",RoleSessionName="UserSession1")
		credentials = assumedRoleObject['Credentials']
		self.ec2 = boto3.client('ec2',
    aws_access_key_id = credentials['AccessKeyId'],
    aws_secret_access_key = credentials['SecretAccessKey'],
    aws_session_token = credentials['SessionToken'],
)

	def startInstance(self):
		try:
			response = self.ec2.start_instances(InstanceIds=[self.instanceID], DryRun=True)
		except ClientError as e:
			if 'DryRunOperation' not in str(e):
				raise
		try:
			response = self.ec2.start_instances(InstanceIds=[self.instanceID], DryRun=False)
			print response
		except ClientError as e:
			print e

	def stopInstance(self):
		try:
			response = self.ec2.stop_instances(InstanceIds=[self.instanceID], DryRun=True)
			print response
		except ClientError as e:
			if 'DryRunOperation' not in str(e):
				raise
		try:
			response = self.ec2.stop_instances(InstanceIds=[self.instanceID], DryRun=False)
			print response
		except ClientError as e:
			print e

	def waitForInstance(self,typeOfWait):
		print "This could take a while.."
		waiter = self.ec2.get_waiter(typeOfWait)
		waiter.wait(Filters=[{'Name':'instance-state-name','Values':['running']}],InstanceIds=[self.instanceID])
		#print typeOfWait + " OK"

	def spawnNewMaster(self):
		response = self.ec2.run_instances(ImageId=self.AWSAmi,MinCount=1,MaxCount=1,InstanceType=self.instanceType,IamInstanceProfile={'Arn': 'arn:aws:iam::214187139358:instance-profile/MasterNodeRole'})#,Placement={'AvailabilityZone':self.regionName})
		for i in response['Instances']:
			print i['ImageId']
			print i['InstanceId']
			self.instanceID = i['InstanceId']
		self.waitForInstance('instance_running')
		self.wait_for_status_check()
		self.publicDNSName = self.ec2.describe_instances(InstanceIds=[self.instanceID])['Reservations'][0]['Instances'][0]['PublicDnsName']

	def getDNS(self):
		self.publicDNSName = self.ec2.describe_instances(InstanceIds=[self.instanceID])['Reservations'][0]['Instances'][0]['PublicDnsName']
		print self.publicDNSName

	def wait_for_status_check(self):
		r = self.ec2.describe_instance_status(InstanceIds=[self.instanceID])
		print "Initializing.."
		while not r['InstanceStatuses'][0]['SystemStatus']['Status'] == 'ok':
			time.sleep(10)
			r = self.ec2.describe_instance_status(InstanceIds=[self.instanceID])


	def getMasterHealth(self):
		response = self.ec2.describe_instances()
		for r in response['Reservations']:
			for i in r['Instances']:
				if i['InstanceId'] == self.instanceID:
					return ['State']['Name']


	def terminateInstance(self):
		print "Terminating instance ID: " + str(self.instanceID)
		self.ec2.terminate_instances(InstanceIds=[self.instanceID])






