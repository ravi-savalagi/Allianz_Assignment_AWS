# Lambda function to control EC2 instances — Flask UI + AWS Lambda

This project provides a Flask-based web interface and an AWS Lambda backend to manage EC2 instances. It allows users to:

Create a new EC2 instance
Start an existing EC2 instance
Stop a running EC2 instance
Terminate an EC2 instance

Architecture
Client (Flask Web UI/Postman) → API Gateway → Lambda → EC2

🗂️ Project Structure
Allianz_Assignment_AWS/
├── src 
        --app.py        # Flask Frontend code
        --lambda_handler.py   # AWS Lambda backend   
├── README.md            # Documentation
├── images
├── requirements        #dependencies
        

⚙️ Setup Instructions
1. Install Dependencies
pip install flask boto3 requests requests-aws4auth

2. Run the Flask App
python app.py

Visit: http://localhost:5000/ec2

🧪 Testing the Lambda Function
✅ Using AWS Lambda Console

Go to AWS Lambda Console.
Select your Lambda function.
Click Test.
Use the following sample payloads:

// Create Instance
{
  "action": "create"
}

// Start Instance
{
  "action": "start",
  "instance_id": "i-xxxxxxxxxxxxxxxxx"
}

// Stop Instance
{
  "action": "stop",
  "instance_id": "i-xxxxxxxxxxxxxxxxx"
}

// Terminate Instance
{
  "action": "terminate",
  "instance_id": "i-xxxxxxxxxxxxxxxxx"
}

📬 Testing via Postman
🔗 API Endpoint
POST https://0bb62kmym8.execute-api.ap-south-1.amazonaws.com/dev_ravi

🔐 Authorization
In the Authorization tab, choose:

Type: AWS Signature
AccessKey: <Your AWS Access Key>
SecretKey: <Your AWS Secret Key>
AWS Region: ap-south-1
Service Name: execute-api

📦 Body (raw JSON)
{
  "action": "create"
}

Or for other actions:
{
  "action": "start",
  "instance_id": "i-xxxxxxxxxxxxxxxxx"
}

🖥️ EC2 Actions via API

ActionPayload ExampleDescriptionCreate{ "action": "create" }Launches a new EC2 instanceStart{ "action": "start", "instance_id": "i-xxxx" }Starts a stopped instanceStop{ "action": "stop", "instance_id": "i-xxxx" }Stops a running instanceTerminate{ "action": "terminate", "instance_id": "i-xxxx" }Terminates an instance

📥 API Responses

✅ Success

{
  "statusCode": 200,
  "body": {
    "message": "Started instance i-xxxx"
  }
}

❌ Error

{
  "statusCode": 400,
  "body": {
    "error": "Missing instanceId"
  }
}

🔐 SSH Details Returned (on Create)
{
  "instance_id": "i-0ba1df1298565f463",
  "public_ip": "3.108.51.119",
  "username": "ec2-user",
  "key_name": "ravi_exampleuser",
  "ssh_command": "ssh -i ravi_exampleuser.pem ec2-user@3.108.51.119"
}

🌐 Web UI Features

Buttons to Create, Start, Stop, Terminate EC2 instances.
Dropdown to select existing instances.
Displays success/error messages.
Shows SSH command and instance details after creation.


🔒 IAM Policy for Lambda Role

{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:RunInstances",
        "ec2:DescribeInstances",
        "ec2:StartInstances",
        "ec2:StopInstances",
        "ec2:TerminateInstances",
        "ec2:CreateTags"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}


