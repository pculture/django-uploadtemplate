from setuptools import setup, find_packages

version = '0.0.1'

setup(
    name="django-uploadtemplate",
    version=version,
    maintainer='Participatory Culture Foundation',
    maintainer_email='dev@mirocommunity.org',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'django>=1.4',
        'PIL>=1.1.7',
    ],
    tests_require=[
        'unittest2>=0.5.1',
        'mock>=0.8.0',
        'tox>=1.4.2',
        'django-nose>=1.1',
    ],
)
