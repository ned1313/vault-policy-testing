# Import the PyYAML
import yaml
import hvac, os, argparse, datetime
from requests import Request, Session

# Create an action to request conversion
request_mapping = {
    "read": "GET",
    "write": "POST",
    "delete": "DELETE",
    "list": "LIST"
}

# Create a test function
def vault_test(test, admin, client):
    # Print the path
    print(test["path"])
    # Check to see if the path exists
    # If path exists, Log it
    # If path does not exist, throw an error
    # Print the action
    print(test["action"])
    s = Session()
    headers = {'X-Vault-Token': client.token}
    req = Request('GET', client.url + "/v1" + test["path"], headers=headers)
    prepped = req.prepare()
    resp = s.send(prepped)
    # Attempt the action on the path
    # Print the expected result
    print(test["result"])
    print(resp.status_code)
    # Compare the expected result to the actual result

# Parse the policy name and test file name from the command line
parser = argparse.ArgumentParser(description='Read a YAML file and test a policy.')
parser.add_argument('-policy','-p', help='The path of the policy file to test.', required=True)
parser.add_argument('-tests','-t', help='The path of the YAML file to test.',required=True)
args = parser.parse_args()

# Verify that the policy file exists
if os.path.isfile(args.policy):
    print("Policy file exists")
else:
    print("Policy file does not exist")
    exit()

# Verify that the YAML file exists
if os.path.isfile(args.tests):
    print("Test file exists")
else:
    print("Test file does not exist")
    exit()

# Connect to Vault
clientAdmin = hvac.Client(url=os.environ['VAULT_ADDR'], token=os.environ['VAULT_TOKEN'])
clientAdmin.is_authenticated()

# Create the policy using a temporary name
policy_name = args.policy.split('.')[0] + "-" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")

# Read the policy file
with open(args.policy) as f:
    policy_content = f.read()

# Create the policy
clientAdmin.sys.create_or_update_policy(name=policy_name, policy=policy_content)

# Create a token that uses the policy
token = clientAdmin.auth.token.create(policies=[policy_name], ttl="10m")
clientPolicy = hvac.Client(url=os.environ['VAULT_ADDR'], token=token["auth"]["client_token"])

# Open the YAML file at the path and load the tests
with open(args.tests) as f:
    tests = yaml.safe_load(f)

for test in tests["tests"]:
    vault_test(test, clientAdmin, clientPolicy)



