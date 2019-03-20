import os
import boto3
import botocore
import json

from troposphere import Ref, Template
import troposphere.ec2 as ec2

class CloudFormation():
    def __init__(self, stack_name, template_name):
        self.stack_name = stack_name
        self.template_name = template_name
        self.cf = boto3.client(
            'cloudformation',
            aws_access_key_id=os.environ['AWS_KEY'],
            aws_secret_access_key=os.environ['AWS_SECRET']
        )

    def instance_tags(self, index):
        tags1 = {"testing": True, "cloudformation":True,"stack":"eddie", "Name": "myinstance1"}
        tags2 = {"testing": True, "cloudformation": True, "stack": "eddie", "Name": "myinstance2"}
        if index ==1:
	        return [ec2.Tag(key, str(value)) for key, value in tags1.items()]
        else:
            return [ec2.Tag(key, str(value)) for key, value in tags2.items()]

    def _stack_exists(self):
        stacks = self.cf.list_stacks()['StackSummaries']
        for stack in stacks:
            if stack['StackStatus'] == 'DELETE_COMPLETE':
                continue
            if self.stack_name == stack['StackName']:
                return True
        return False

    def create_stack_template(self):
        "sg-006bb1b84c5a7ea6c"
        ami_id="ami-0de53d8956e8dcf80"
        t = Template()
        instance = ec2.Instance("myinstance1")
        instance.ImageId = ami_id
        instance.SecurityGroupIds = [ "sg-006bb1b84c5a7ea6c" ]
        instance.InstanceType = "t1.micro"
        instance.Tags = self.instance_tags(1)

        instance2 = ec2.Instance("myinstance2")
        instance2.ImageId = ami_id
        instance2.SecurityGroupIds = [ "sg-006bb1b84c5a7ea6c" ]
        instance2.InstanceType = "t1.micro"
        instance2.Tags = self.instance_tags(2)


        t.add_resource(instance)
        t.add_resource(instance2)

        print(t.to_yaml())
        with open(self.template_name, 'wb') as f:
            f.write(t.to_yaml())

        with open(self.template_name) as template_fileobj:
            template_data = template_fileobj.read()
        self.cf.validate_template(TemplateBody=template_data)
        params = {
            'StackName': self.stack_name,
            'TemplateBody': template_data,
            'Parameters': [],
        }

        try:
            if self._stack_exists():
                print('Updating {}'.format(self.stack_name))
                stack_result = self.cf.update_stack(**params)
                waiter = self.cf.get_waiter('stack_update_complete')
            else:
                print('Creating {}'.format(self.stack_name))
                stack_result = self.cf.create_stack(**params)
                waiter = self.cf.get_waiter('stack_create_complete')
            print("...waiting for stack to be ready...")
            waiter.wait(StackName=self.stack_name)
        except botocore.exceptions.ClientError as ex:
            error_message = ex.response['Error']['Message']
            if error_message == 'No updates are to be performed.':
                print("No changes")
            else:
                raise

    def run(self):
        self.create_stack_template()


if __name__ == '__main__':
    cloud_formation = CloudFormation('eddie-test', 'eddie-test-stack.yaml')
    cloud_formation.run()