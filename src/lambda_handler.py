import json
import boto3
 
ec2 = boto3.client('ec2')
 
def lambda_handler(event, context):
    action = event.get('action')
    instance_id = event.get('instance_id')
   
    try:
        if action == 'start':
            if not instance_id:
                return response(400, 'Missing "instanceId" for start')
 
            # Check current state
            desc = ec2.describe_instances(InstanceIds=[instance_id])
            state = desc['Reservations'][0]['Instances'][0]['State']['Name']
 
            if state == 'stopped':
                ec2.start_instances(InstanceIds=[instance_id])
                return response(200, f'Started instance {instance_id}')
            elif state == 'running':
                return response(200, f'Instance {instance_id} is already running')
            elif state == 'stopping':
                return {
                    "statusCode": 202,
                    "body": json.dumps({
                        "message": f"Instance {instance_id} is currently stopping. Please try starting it again shortly."
                    })
                }
 
            elif state in ['shutting-down', 'terminated']:
               
                return {
                    "statusCode": 400,
                    "body": json.dumps({
                        "error": f"Cannot start instance {instance_id} because it is in state: {state}"
                    })
                }
            else:
                return {
                    "statusCode": 400,
                    "body": json.dumps({
                        "error": f"Cannot start instance in state: {state}"
                    })
                }
 
        elif action == 'stop':
            if not instance_id:
                return response(400, 'Missing "instanceId" for stop')
 
            try:
                desc = ec2.describe_instances(InstanceIds=[instance_id])
                state = desc['Reservations'][0]['Instances'][0]['State']['Name']
 
                if state == 'running':
                    ec2.stop_instances(InstanceIds=[instance_id])
                    return response(200, f'Stopped instance {instance_id}')
                elif state == 'stopped':
                    return response(200, f'Instance {instance_id} is already stopped')
                elif state == 'terminated':
                    return response(400, f'Cannot stop instance {instance_id} because it is terminated')
                else:
                    return response(400, f'Cannot stop instance in state: {state}')
            except Exception as e:
                return response(500, f'Error: {str(e)}')
 
 
        elif action == 'terminate':
            if not instance_id:
                return response(400, 'Missing "instanceId" for terminate')
 
            try:
                desc = ec2.describe_instances(InstanceIds=[instance_id])
                state = desc['Reservations'][0]['Instances'][0]['State']['Name']
 
                if state == 'terminated':
                    return response(400, f'Instance {instance_id} is already terminated')
                else:
                    ec2.terminate_instances(InstanceIds=[instance_id])
                    return response(200, f'Terminated instance {instance_id}')
            except Exception as e:
                return response(500, f'Error: {str(e)}')
 
       
 
        elif action == 'create':
            key_name = 'ravi_exampleuser'
            new_instance = ec2.run_instances(
            ImageId='ami-01b6d88af12965bb6',
            InstanceType='t2.micro',
            MinCount=1,
            MaxCount=1,
            KeyName=key_name,
            SecurityGroupIds=['sg-05ed527a725f94f65']
            )
            instance = new_instance['Instances'][0]
            instance_id = instance['InstanceId']
 
            # Wait for instance to be running and get public IP
            waiter = ec2.get_waiter('instance_running')
            waiter.wait(InstanceIds=[instance_id])
 
            # Fetch instance details
            desc = ec2.describe_instances(InstanceIds=[instance_id])
            public_ip = desc['Reservations'][0]['Instances'][0].get('PublicIpAddress')
            ssh_command = f"ssh -i {key_name}.pem ec2-user@{public_ip}"
            ssh_info = {
                "instance_id": instance_id,
                "public_ip": public_ip,
                "username": "ec2-user",  
                "key_name": "ravi_exampleuser",
                "ssh_command":ssh_command
               
            }
 
            return response(200, ssh_info)
 
 
        else:
            return response(400, 'Invalid action. Use start, stop, terminate, or create.')
 
    except Exception as e:
        return response(500, f'Error: {str(e)}')
 
 
def response(status, message):
    return {
        'statusCode': status,
        'body': json.dumps(message)
    }
 
