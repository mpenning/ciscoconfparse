# Old fabric v1 methods:
# from fabric.api import run, local, cd, lcd, put, settings
from getpass import getpass
import sys
import os

from fabric import Connection
from invoke import run


def deploy_ccp_docs(
    ccp_doc_root="public_html/py/ciscoconfparse",
    ccp_bundle_name="ccp.tar.gz",
    doc_host="",
    password="",
):
    """
    Build and push ciscoconfparse documentation to public webhost
    """

    # Run 'make html' in directory: sphinx-doc/
    run("cd sphinx-doc && make clean && make html")  # local command

    run(
        "cd sphinx-doc/_build/html && tar cvfz {} *".format(
            os.path.expanduser("~/" + ccp_bundle_name)
        )
    )

    # Run 'make clean' in directory: sphinx-doc/
    run("cd sphinx-doc && make clean")  # local command

    # ssh with a password...
    conn = Connection(
        "mpenning@{}".format(doc_host), connect_kwargs={"password": password}
    )
    conn.put(
        local=os.path.expanduser("~/{}".format(ccp_bundle_name)),
        remote=ccp_bundle_name,
    )

    # Delete all the old files
    conn.run("rm -rf {}/*".format(ccp_doc_root))
    # Move the new files to ccp_doc_root
    conn.run("mv {} {}".format(ccp_bundle_name, ccp_doc_root))

    with conn.cd(ccp_doc_root):
        conn.run("tar xvfz {}".format(ccp_bundle_name))
        conn.run("rm {}".format(ccp_bundle_name))


if __name__ == "__main__":
    doc_host = input("Documentation host: ")
    password = getpass()
    deploy_ccp_docs(doc_host=doc_host.strip(), password=password)
