# Contributing to Shipt/py-volley

## Welcome
We are glad you are here! We think it's awesome that you want to spend time helping us make Volley even better. We really value the community we get to be a part of, and we are grateful for your contribution.

Contribution requires signing a Contributor License Agreement (CLA) via HelloSign, a process automated as a part of a pull request.  Your Github email address must match the email address used to sign the CLA. Github has [documentation](https://help.github.com/articles/setting-your-commit-email-address-on-github/) on setting email addresses. Your git email must also match this email address.

The basic recommended workflow:
1. Fork Volley
2. Setup your development environment. It is recommended to use `make setup` or `poetry install`.
3. Start a new branch for your feature
    * We are not picky about branch prefixes. But generally:
      * `/username/<featureName>`: for features
      * `/username/<fixName>`: for general refactoring or bug fixes
4. Submit a Draft Pull Request. Do it early and mark it `WIP` so a maintainer knows it's not ready for review just yet.
    * tests and CI gates must pass. You can run most on your localhost with `make lints`, `make test.unit`, `make test.integration`. `make format` will auto-format much of your code to the project's standards.
5. If you haven't signed our CLA before, then you will receive an email from HelloSign to sign the CLA.
    * The CLA request will be sent to the email address associated with your github account.
    * You cannot have your PR merged without signing the PR.
    * If you already submitted a PR and need to correct your user.name and/or user.email please do so and then use `git commit --amend --reset-author` and then `git push --force` to correct the PR.
6. Request review from one of our maintainers. 
7. Get Approval. We'll let you know if there are any changes that are needed. 
8. Merge your changes into Vollley.

Pull Requests: 
- Submit a PR to get your changes approved
- Review from [maintainer](MAINTAINERS.md) should happen automatically via `.github/CODEOWNERS`
- Make sure you include an explanation of what's changed, why, and anything these changes affect 
- Tests and Code Quality gates will run and must pass
- Our maintainer will review and approve your PR 
- Merge!

## Community Guidelines
  1. Be Kind
    - Working with us should be a fun learning opportunity, and we want it to be a good experience for everyone. Please treat each other with respect.  
    - If something looks outdated or incorrect, please let us know! We want to make Volley as useful as possible. 
  2. Own Your Work
     * Creating a PR for Volley is your first step to becoming a contributor, so make sure that you own your changes. 
     * Our maintainers will do their best to respond to you in a timely manner, but we ask the same from you as the contributor. 

## _Thank you!_