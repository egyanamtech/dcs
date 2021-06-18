import sys
import os
import shutil
import setuptools

if sys.argv[-1] == "publish":
    # if os.system("pip freeze | grep wheel"):
    #     print("wheel not installed.\nUse `pip install wheel`.\nExiting.")
    #     sys.exit()
    if os.system("pip freeze | grep twine"):
        print("twine not installed.\nUse `pip install twine`.\nExiting.")
        sys.exit()
    os.system("python setup.py sdist bdist_wheel")
    os.system("twine upload dist/*")
    shutil.rmtree("dist")
    shutil.rmtree("build")
    # shutil.rmtree("djangorestframework.egg-info")
    sys.exit()

setuptools.setup()
