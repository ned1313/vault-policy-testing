# Testing Vault Policies with Python

Here's the big idea. When you create a new set of Vault policies, you should be able to write tests that confirm your intention. The tests should be easy to write and can be run against a development Vault server that mimics production, or against the production environment, without altering the production environment beyond adding temporary policies.

## Pieces of functionality

Let's start with the testing process. Each policy will have a corresponding test file written in `yaml` that describes the tests to run against the policy. The test file will contain a series of tests that confirm the policy works as intended. The tests will leverage the `sys/capabilities` endpoint to confirm the policy is working as intended.

The test suite will run as part of a CI/CD process. I imagine that initial tests should be able to run locally, creating a temporary development Vault server. Once the policies are committed to the repository and a pull request is created, the test suite will run against a production Vault server (maybe, have to be careful about this part) or against a temporary dev server, depending on the user's preference. The test suite could be run against the production Vault server before a pull request is merged.

## Defining the tests

Each test should include the following:

* `path` - The path to be tested
* `actions` - List of action(s) to test
* `result` - The desired result of the action
  * `true` - the action(s) are allowed
  * `false` - the action(s) are denied

Each test will be a be represented as a map with the `path`, `actions`, and `result` keys. The script will iterate through each test and return a pass or fail result. This will be based on the capabilities response from Vault. If the action is in the capabilities response and the desired result is `true`, the test passes. If the action is not in the capabilities response, and the desired result is `false`, the test passes. Otherwise the test will fail.

Here's an example of the test file format:

```yaml
tests:
  - path: 'secret/data/taco'
    actions: [read]
    result: false
  - path: 'secret/data/taco'
    actions: [update]
    result: false
  - path: 'secret/data/taco/recipe'
    actions: [read, list]
    result: true
```

The Vault namespace, address, and token can defined as part of the run process using environment variables. The script will use the `VAULT_ADDR` and `VAULT_TOKEN` environment variables to connect to Vault. The `VAULT_NAMESPACE` environment variable will be used to set the namespace. If the namespace is not set, the script will use the root namespace.

The Python file `test_capabilities.py` will be used to run the tests. The script will take the following arguments:

* `-p` or `-path` - the path to the policy file
* `-t` or `-tests` - the path to the test file
* `-d` or `-directory` - the path to a directory containing multiple policy files (assumes test files are in a `tests` subdirectory)
* `-v` or `-vaultdev` - spins up a temporary Vault dev server (assumes vault executable is in the `PATH`)
* `-j` or `-jsonout` - writes the policies being tested to JSON files in the current working directory (useful for OPA testing)

During the testing process, the script will use the token stored in `VAULT_TOKEN` to create a temporary policy and token with that policy. Then the script will use the `sys/capabilities` and token to test the policy.

The script also checks to see if the tested path is `root` protected, and thus needs the `sudo` action. If the `sudo` action is not found in the capabilities response for a `root` protected path and the `result` is supposed to be `true`, the script will fail the test.

The list of `root` protected paths is defined in the `sudo_paths.json` file. The list can be updated as needed.

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

Run the script to spin up a temporary Vault dev instance and test one of the existing policies:

```bash
python test_capabilities.py -p ".\policies\taco.hcl" -t ".\policies\tests\taco.yaml" -v
```

You can also test all the policies in a directory:

```bash
python test_capabilities.py -d ".\policies" -v
```

You can update the contents of the `taco.hcl` and `taco_test.yaml` files to test different policies and actions.
