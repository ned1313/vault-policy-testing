# Testing Vault Policies with Python

Here's the big idea. When you create a new set of Vault policies, you should be able to write tests that confirm your intention. The tests should be easy to write and can be run against a development Vault server that mimics production, or against the production environment, without altering the production environment beyond adding temporary policies.

## Pieces of functionality

Let's start with the testing process. Each policy will have a corresponding test file with the same name and `_test.yaml` appended. Maybe we can place it in a `test` directory too? The test file will contain a series of tests that confirm the policy works as intended. The tests will leverage the `sys/capabilities` endpoint to confirm the policy is working as intended.

The test suite will run as part of a CI/CD process. I imagine that initial tests should be able to run locally, creating a temporary development Vault server. Once the policies are committed to the repository and a pull request is created, the test suite will run against a production Vault server (maybe, have to be careful about this part). The test suite will be run against the production Vault server before the pull request is merged.

The tests should only be run against policies that have been changed. A simple git diff should help determine that.

## Defining the tests

Each test should include the following:

* The path to be tested
* The action to execute
* The desired result of the action
  * `true` - the action is allowed
  * `false` - the action is denied

Each test will be a be represented as a map with the `path`, `action`, and `result` keys. The script will iterate through each test and return a pass or fail result. This will be based on the capabilities response from Vault. If the action is in the capabilities response and the desired result is `true`, the test passes. If the action is not in the capabilities response, and the desired result is `false`, the test passes. Otherwise the test will fail.

Here's an example of the test file format:

```yaml
tests:
  - path: 'secret/data/taco'
    action: read
    result: true
  - path: 'secret/data/taco'
    action: write
    result: false
```

The Vault namespace and address will be defined as part of the run process, and will not be included in the test file. The Python test should be a simple loop that iterates through the tests and executes them against the Vault server.

The current `taco_test.py` file is a proof of concept using the `hvac` library for the Vault client. Currently, it can create two client instances, one for an admin token and another for the policy being tested. The admin client will need to be able to create policies and tokens and access the `sys/capabilities` endpoint. The policy token is assigned the policy being tested and will be used as part of the endpoint request.

When the testing is complete, the policy token will be revoked and the temporary policy will be removed.

## Running the software

You should start by creating a virtual environment and installing the dependencies:

```bash
python -m venv venv

# Linux
source venv/Scripts/activate

# Windows
.\venv\Scripts\Activate.ps1
```

And install the dependencies:

```bash
pip install -r requirements.txt
```

Next, start up an instance of Vault in dev mode:

```bash
vault server -dev
```

In another terminal, export the Vault address and token:

```bash
# Linux
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='TOKEN_VALUE'

# Windows
$env:VAULT_ADDR='http://127.0.0.1:8200'
$env:VAULT_TOKEN='TOKEN_VALUE'
```

And create the necessary secret in Vault:
  
```bash
vault kv put secret/taco sauce=verde
```

Finally, run the test script:

```bash
python test_capabilities.py -p taco.hcl -t taco_test.yaml
```

You can update the contents of the `taco.hcl` and `taco_test.yaml` files to test different policies and actions.
