# Import the PyYAML
import yaml, json, uuid
import hvac, os, argparse, datetime, hcl, glob
import subprocess, logging, re
from requests import Request, Session

def test_capabilities(test, admin, client, policy_name):
    test_result = {
        "policy_name": policy_name,
        "path": test["path"],
        "test_result": "fail",
        "desired_result": test["result"],
        "input_actions": test["actions"],
        "actual_actions": [],
        "message": "Test failed for unknown reason"
    }
    # Log the the action
    logging.info(test["actions"])
    s = Session()
    headers = {'X-Vault-Token': admin.token}
    payload = '''
    {
        "token": "%s",
        "paths": ["%s"]
    }
    ''' % (client.token, test["path"])
    logging.info(payload)

    req = Request('POST', admin.url + "/v1/sys/capabilities", headers=headers, data=payload)
    prepped = req.prepare()
    resp = s.send(prepped)
    
    capabilities = resp.json()["capabilities"]
    test_result["actual_actions"] = capabilities
    logging.info(capabilities)

    # Check if sudo is required
    sudo_required = needs_sudo(test["path"], capabilities)

    # So capture the intersection first and apply the two tests
    intersection = set(test["actions"]).intersection(set(capabilities))
    # If the desired result is true, the intersection of the policy and capabilities should be the same as the policy
    if test["result"]:
        if sudo_required and "sudo" not in capabilities:
            test_result["message"] = "Test failed: " + policy_name + " does not have sudo capability on " + test["path"]
            test_result["test_result"] = "fail"
        elif intersection == set(test["actions"]):
            test_result["message"] = "Test passed: " + policy_name + " has [" + ' '.join(test["actions"]) + "] capabilities on " + test["path"]
            test_result["test_result"] = "pass"
        else:
            test_result["message"] = "Test failed: " + policy_name + " does not have some of [" + ' '.join(test["actions"]) + "] capabilities on " + test["path"]
            test_result["test_result"] = "fail"

    # If the desired result is false, the intersection of the policy and capabilities should be empty
    else:
        if intersection == set():
            test_result["message"] = "Test passed: " + policy_name + " does not have [" + ' '.join(test["actions"]) + "] capabilities on " + test["path"]
            test_result["test_result"] = "pass"
        else:
            test_result["message"] = "Test failed: " + policy_name + " has some of [" + ' '.join(test["actions"]) + "] capabilities on " + test["path"]
            test_result["test_result"] = "fail"

    # Log the result of the test
    logging.info(test_result["message"])

    return test_result

# Convert the policy file to JSON and write to file
def policy_to_json(policy_file):
    json_file = policy_file + ".json"
    with open(policy_file) as f:
        load_policy = hcl.load(f)
    with open(json_file, 'w') as f:
        f.write(hcl.dumps(load_policy))

def prepare_policy(policy_file_path, test_file_path, admin):
    # Create the policy using a temporary name
    policy_name = os.path.basename(policy_file_path)
    temp_policy_name = policy_name.split('.')[0] + "-" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    # Read the policy file
    with open(policy_file_path) as f:
        policy_content = f.read()

    # Create the policy
    admin.sys.create_or_update_policy(name=temp_policy_name, policy=policy_content)
    
    # Create a token that uses the policy
    token = admin.auth.token.create(policies=[temp_policy_name], ttl="10m")
    clientPolicy = hvac.Client(url=os.environ['VAULT_ADDR'], token=token["auth"]["client_token"])

    # Open the YAML file at the path and load the tests
    with open(test_file_path) as f:
        tests = yaml.safe_load(f)
    
    results = []
    
    for test in tests["tests"]:
        results.append(test_capabilities(test, admin, clientPolicy, policy_name))

    # Delete the policy
    logging.info("Deleting temporary policy")
    admin.sys.delete_policy(name=temp_policy_name)

    # Return results
    return results

def needs_sudo(test_path,test_actions):
    # Check if the test path starts with one of the paths that needs sudo
    if test_path.split('/')[0] in sudo_policy_paths["sudo_prefixes"]:
        logging.info(test_path + " starts with a sudo prefix")
        # Check each path in the sudo policy paths
        for sudo_path in sudo_policy_paths["sudo_paths"]:
            # If the test path starts with the sudo path, check actions
            if re.search(sudo_path["path"], test_path):
                logging.info(test_path + " matched with " + sudo_path["path"])
                if set(test_actions).intersection(set(sudo_path["actions"])) != set():
                    logging.info("Sudo required")
                    return True
    return False

def set_multiline_output(name, value):
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        delimiter = uuid.uuid1()
        print(f'{name}<<{delimiter}', file=fh)
        print(value, file=fh)
        print(delimiter, file=fh)
    
# Parse the arguments
parser = argparse.ArgumentParser(description='Read policies and tests. Can be individual policies or a directory of policies.')
# Policy set 1 is the policy and the test files
parser.add_argument('-policy','-p', help='The path of the policy file to test. Use with -tests.', required=False)
parser.add_argument('-tests','-t', help='The path of the YAML file to test. Use with -policy.',required=False)

# Argument set 2 is the directory of policies and the test files
parser.add_argument('-directory','-d', help='The path of the directory of policies to test. Use alone.',required=False)

# Launch a Vault dev server instance for testing
parser.add_argument('-vaultdev','-v', help='Launch a Vault dev server instance for testing.',required=False, action='store_true')

# Write out policies to JSON files
parser.add_argument('-jsonout','-j', help='Write out policies to JSON files.',required=False, action='store_true')

args = parser.parse_args()

# Check that either policy and test are set or directory is set
if args.policy and args.tests and not args.directory:
    logging.info("Policy and test file arguments set")
    argumentSet = 1
elif args.directory and not args.policy and not args.tests:
    logging.info("Directory argument set")
    argumentSet = 2
else:
    logging.error("Invalid arguments set, use -h for help")
    exit()

if args.vaultdev:
    vault_process = subprocess.Popen(["vault", "server", "-dev", "-dev-root-token-id=1234567890QWERTYUIOPasdfghjkl"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    os.environ['VAULT_ADDR'] = "http://127.0.0.1:8200"
    os.environ['VAULT_TOKEN'] = "1234567890QWERTYUIOPasdfghjkl"
    logging.info("Vault dev server launched")
    logging.info(vault_process.pid)

# Verify that the policy and test files exist
if argumentSet == 1:
    if os.path.isfile(args.policy):
        logging.info("Policy file exists")
    else:
        logging.error("Policy file does not exist")
        exit()
    
    if os.path.isfile(args.tests):
        logging.info("Test file exists")
    else:
        logging.error("Test file does not exist")
        exit()

# Verify that the directory exists and has correct structure
if argumentSet == 2:
    if os.path.isdir(args.directory):
        logging.info("Directory exists")
    else:
        logging.error("Directory does not exist")
        exit()
    # Verify that the directory has a policy and test file
    policy_files = glob.glob(args.directory + "/*.hcl")
    test_files = glob.glob(args.directory + "/tests/*.yaml")
    if policy_files and test_files:
        logging.info("Policy and test files exist in selected directory")
    else:
        logging.error("Policy and test files do not exist in selected directory")
        exit()

# Connect to Vault
clientAdmin = hvac.Client(url=os.environ['VAULT_ADDR'], token=os.environ['VAULT_TOKEN'])
clientAdmin.is_authenticated()

# Load sudo policy path data
with open('sudo_paths.json') as f:
    sudo_policy_paths = json.load(f)

if argumentSet == 1:
    results = prepare_policy(args.policy, args.tests, clientAdmin)
    print(results)

    if args.jsonout:
        policy_to_json(args.policy)

if argumentSet == 2:
    all_tests = []
    policies_full_path = os.path.abspath(args.directory)
    policy_files = glob.glob(policies_full_path + "/*.hcl")
    for policy_file in policy_files:
        logging.info(policy_file)
        test_file = os.path.dirname(policy_file) + "/tests/" + os.path.basename(policy_file).split('.')[0] + ".yaml"
        logging.info(test_file)
        if os.path.isfile(test_file):
            results = prepare_policy(policy_file, test_file, clientAdmin)
            all_tests.extend(results)
        else:
            logging.warning("Test file does not exist for " + policy_file +". Skipping policy testing.")
        if args.jsonout:
            policy_to_json(policy_file)
    logging.info("All tests completed")
    print(json.dumps(all_tests))

    if os.getenv("GITHUB_ACTIONS") != None:
        set_multiline_output("test_results", json.dumps(all_tests))

if args.vaultdev:
    logging.info("Killing Vault dev server")
    vault_process.terminate()
