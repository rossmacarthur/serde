Contributing
============

Contributions are welcome, and they are greatly appreciated!

Reporting Bugs
--------------

Report bugs to https://github.com/rossmacarthur/serde/issues.

Please include the following information:

- Detailed steps and/or code to reproduce the bug.
- What version of Python you are using.
- Anything else relevant about your Python environment and operating system that
  could be useful for troubleshooting.

If you have the chance, before reporting a bug, please search existing issues,
as it's possible that someone else has already reported your error. It's fine if
you accidentally file a duplicate report.

Pull Requests
-------------

If you would like to fix a bug, implement a feature, or simply improve this
project's documentation then you should fork this repository and submit a pull
request.

Guidelines
~~~~~~~~~~

Your pull request needs to meet the following guidelines:

- Includes tests for the code you are adding.
- Passes all lints and tests.
- Builds on all supported Python versions.
- Updates the documentation and RELEASES file where relevant.

Development process
~~~~~~~~~~~~~~~~~~~

1. Fork the `serde`_ repository on GitHub.

2. Clone your fork locally::

    git clone git@github.com:your_name_here/serde.git

3. Setup and activate your virtualenv using pyenv, virtualenvwrapper, or
   similar. You can use ``make install-all`` to install the package and all
   development dependencies into your virtualenv.

4. Create a branch for local development::

    git checkout -b name-of-your-bugfix-or-feature

5. Make your changes locally.

6. Run all lints using ``make lint``.

7. Run all tests using ``make test``.

8. Commit your changes and push your branch to GitHub::

    git add .
    git commit -m "A detailed description of your changes"
    git push origin name-of-your-bugfix-or-feature

9. Submit a pull request on GitHub.

.. _serde: https://github.com/rossmacarthur/serde
