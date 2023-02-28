# Testing Vault Policies with Python

Here's the big idea. When you create a new set of Vault policies, you should be able to write tests that confirm your intention. The tests should be easy to write and can be run against a development Vault server that mimics production, or against the production environment, without altering the production environment beyond adding temporary policies and secrets.

## Pieces of functionality

Let's start with the testing process. Each policy will have a corresponding test file with the same name and `_test.py` appended. Maybe we can place it in a `test` directory too? The test file will contain a series of tests that confirm the policy works as intended. The tests will be written in Python, using the `pytest` framework. The tests will be run against a Vault server. If any of the tests fail, the test suite will fail.

The test suite will run as part of a CI/CD process. I imagine that initial tests should be able to run locally, creating a temporary development Vault server. Once the policies are committed to the repository and a pull request is created, the test suit will run against a production Vault server. The test suite will be run against the production Vault server before the pull request is merged.

The tests should only be run against policies that have been changed. A simple git diff should help determine that.

## Defining the tests

Each test should include the following:

* The path to be tested
* The actions to execute
* The expected responses from Vault

Each test will be a map of actions against a single path on the Vault server. The map of actions will be the action name and the expected response. For example: `{"read": "200"}` or `{"write": "403"}`. The expected response will be the HTTP status code returned by Vault. A full test should look something like this:

```yaml
tests:
    - path: secret/data/test
        actions:
        - read: 200
        - write: 403
```

The Vault namespace and address will be defined as part of the run process, and will not be included in the test file. The Python test should be a simple loop that iterates through the actions and executes them against the Vault server. Some of the actions may require dummy data, and I'm not sure how to handle that yet. Can we send an empty string as data and see if we get a 403 response? I'm not sure. Otherwise, we'll need mock data for each path type and that gets complicated quickly.

