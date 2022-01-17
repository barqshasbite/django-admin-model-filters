# coding=utf-8

"""Model filters packaging."""

import fnmatch

from setuptools import find_packages, setup
from setuptools.command.build_py import build_py


class ExcludeFileBuilder(build_py):
    """Exclude files that match patterns."""

    excluded = [
        "*_tests.py",
        "*local_settings.py",
    ]

    def find_package_modules(self, package, package_dir):
        """Exclude package modules whose path match the excluded patterns."""
        modules = super().find_package_modules(package, package_dir)
        return [
            (pkg, mod, file)
            for (pkg, mod, file) in modules
            if not any(
                fnmatch.fnmatchcase(str(file), pat=pattern) for pattern in self.excluded
            )
        ]


setup(
    name="django-admin-model-filters",
    url="https://github.com/barqshasbite/django-admin-model-filters",
    packages=find_packages(
        exclude=["acme", "acme.*", "scripts", "scripts.*", "tests", "tests.*"]
    ),
    include_package_data=True,
    cmdclass={"build_py": ExcludeFileBuilder},
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: Django",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
)
