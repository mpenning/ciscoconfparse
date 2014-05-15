from fabric.api import run, local, cd, lcd, put, settings
# See:
#     http://docs.fabfile.org/en/latest/api/core/operations.html

def deploy_ccp_docs(ccp_doc_root="public_html/py/ciscoconfparse",
    ccp_bundle_name="ccp.tar.gz", doc_host=""):

    with lcd('sphinx-doc'):
        local('make html')  # local command

    with lcd('sphinx-doc/_build/html'):
        local('tar cvfz ~/{0} *'.format(ccp_bundle_name))

    with lcd('sphinx-doc'):
        local('make clean')

    with settings(host_string=doc_host):
        # scp file to server
        put(local_path="~/{0}".format(ccp_bundle_name), 
            remote_path=ccp_bundle_name)
        with cd(ccp_doc_root):
            run("rm -rf *")  # Remote command
            run("mv ~/{0} .".format(ccp_bundle_name))
            run("tar xvfz {0}".format(ccp_bundle_name))
            run("rm {0}".format(ccp_bundle_name))

if __name__=="__main__":
    doc_host = raw_input("Documentation host: ")
    deploy_ccp_docs(doc_host=doc_host.strip())
