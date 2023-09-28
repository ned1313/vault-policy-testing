# List of Improvements

* Update function to evaluate multiple actions at once
  * Done! Changed the YAML to use actions list instead of single action
* Return usable JSON data for CI/CD integration
  * Done: writes files to CWD with -j argument
* Test missing backends
* Test more complex policies
* Add option to spin up Dev server auto-magically
  * Done: use the `-v` flag
* Clean up print statements
* Add logging
* Convert HCL to JSON for OPA: https://pypi.org/project/pyhcl/
  * Done: use the `-j` flag
* Add support for multiple policies using a folder structure
  * Done: use the `-d` flag
* Check against sudo policies
