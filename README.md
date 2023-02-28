# Testing Vault Policies with Python

Here's the big idea. When you create a new set of Vault policies, you should be able to write tests that confirm your intention. The tests should be easy to write and can be run against a development Vault server that mimics production, or against the production environment, without altering the production environment beyond adding temporary policies and secrets.

## Pieces of functionality

Let's start with the testing process. Each policy will have a corresponding test file with the same name and `_test.yaml` appended. Maybe we can place it in a `test` directory too? The test file will contain a series of tests that confirm the policy works as intended. The tests will be written in Python, maybe using the `pytest` framework (more research is required). The tests will be run against a Vault server. If any of the tests fail, the test suite will fail.

The test suite will run as part of a CI/CD process. I imagine that initial tests should be able to run locally, creating a temporary development Vault server. Once the policies are committed to the repository and a pull request is created, the test suite will run against a production Vault server (maybe, have to be careful about this part). The test suite will be run against the production Vault server before the pull request is merged.

The tests should only be run against policies that have been changed. A simple git diff should help determine that.

## Defining the tests

Each test should include the following:

* The path to be tested
* The action to execute
* The result of the action (`true` or `false`)

Each test will be a be represented as a map with the `path`, `action`, and `result` keys. Generally, a status code from Vault of `200` should be equal a `true` result, and `400` code will equal a `false` result. Any other status code would throw an error. A full test should look something like this:

```yaml
tests:
  - path: 'secret/data/taco'
    action: read
    result: true
  - path: 'secret/data/taco'
    action: write
    result: false
```

We may need to add more keys to each test to set up the test and identify the path type. For example, the `write` action may be against a `kvv2` backend or an `aws` backend. The testing suite needs to know how to handle each backend type to send a valid request, and possibly instantiate a temporary backend.

The Vault namespace and address will be defined as part of the run process, and will not be included in the test file. The Python test should be a simple loop that iterates through the tests and executes them against the Vault server. Some of the tests may require dummy data, and I'm not sure how to handle that yet. Can we send an empty string as data and see if we get a 403 response? I'm not sure. Otherwise, we'll need mock data for each backend type and that gets complicated quickly. I'm imagining we could create a Python library for each backend type that would handle the mock data creation and request execution.

The current `read_yaml.py` file is a proof of concept using the `hvac` library for the Vault client. Currently, it can create two clients instance, one for an admin token and another for the policy being tested. The admin client will need to be able to create policies and tokens, and possibly create backends and place data. The policy token is assigned the policy being tested and will be used to execute the tests.

Right now, the test only handles the kvv2 backend and assumes the data is already present at the path.
