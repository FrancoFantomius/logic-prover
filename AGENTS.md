This are the rules to follow when coding in this repository.

1. Do not regenerate the documentation, there is an action that does that automatically.
2. Do not run the test suite when exploring a repo.
3. Do not modify the precedent versions of the CHANGELOG.md file. This should be a record so only write for the current version.
4. After having implemented a change run the test suite only if the changes are in the ./logic_prover subfolder.
5. If a test does not pass after your implementation you MUST fix the implementation NOT the test.
6. Every change MUST be documented, the documentation to each function should be written under the name line. There should be a short explanation, a presentation of the variables with their type and default values (if any), it should end with the output type and an example if applicable.

-----

What follows are the task to check when the user wants to publish a new version of the package. These should be checked in order and not skipped:

1. Bump the version in pyproject.toml to x.y+1.z if this is a major release or x.y.z+1 if this is a minor release, where x.y.z is the current version of the package.
2. The version of the package.json and pyproject.toml files should match and be 
3. Update CHANGELOG.md with the changes made.
4. Add a tag with the new version to git.
5. Run all the tests and verify that they pass.
6. Update the status badge in the README.md file and update anything accordingly.
7. Update the SECURITY.md file with the version and any other change necessary.

-----

What follows are the tasks to check when the user asks to check a file or folder:

1. Explore the folder/file making a list of each function or class.
2. For each item in the list check if it is used or can be deprecated, check that it is coherent with the request made and the other functions of the list.
3. For each item in the list check the correctness of the documentation and that it adheres to the standard defined in rule #6.
4. Write a report/implementation plan explaining what is needed to change.