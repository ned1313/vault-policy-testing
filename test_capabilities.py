# Import the PyYAML
import yaml
import hvac, os, argparse, datetime
from requests import Request, Session

def test_capabilities(test, admin, client, policy_name):
    test_result = {
        "result": "fail",
        "message": "Test failed for unknown reason"
    }
    # Print the action
    print(test["action"])
    s = Session()
    headers = {'X-Vault-Token': admin.token}
    payload = '''
    {
        "token": "%s",
        "paths": ["%s"]
    }
    ''' % (client.token, test["path"])
    print(payload)

    req = Request('POST', admin.url + "/v1/sys/capabilities", headers=headers, data=payload)
    prepped = req.prepare()
    resp = s.send(prepped)
    
    capabilities = resp.json()["capabilities"]
    print(capabilities)

    if test["action"] in capabilities:
        if test["result"]:
            test_result["message"] = "Test passed: " + policy_name + " has " + test["action"] + " capabilities on " + test["path"]
            test_result["result"] = "pass"
        if not test["result"]:
            test_result["message"] = "Test failed: " + policy_name + " has " + test["action"] + " capabilities on " + test["path"]
    else:
        if test["result"]:
            test_result["message"] = "Test failed: " + policy_name + " does not have " + test["action"] + " capabilities on " + test["path"]
        if not test["result"]:
            test_result["message"] ="Test passed: " + policy_name + " does not have " + test["action"] + " capabilities on " + test["path"]
            test_result["result"] = "pass"

    # Print the expected result
    print(test_result["message"])

    return test_result
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

results = []

for test in tests["tests"]:
    results.append(test_capabilities(test, clientAdmin, clientPolicy, policy_name))


print(results)

# Revoke the client token
clientPolicy.auth.token.revoke_self()

# Delete the policy
clientAdmin.sys.delete_policy(name=policy_name)
