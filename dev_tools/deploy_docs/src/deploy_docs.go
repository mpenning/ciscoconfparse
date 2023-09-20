package main

import (
	"github.com/gleich/logoru"
	"github.com/melbahja/goph"
)

func main() {

	logoru.Info("Starting Documentation build")

	logoru.Info("Starting CiscoConfParse new documentation upload")

	logoru.Info("    Initialize ssh key-auth")
	// Start new ssh connection with private key.
	auth, err := goph.Key("/home/mpenning/.ssh/id_ed25519", "")
	if err != nil {
		logoru.Critical(err.Error())
	}

	logoru.Debug("    ssh into remote webhost")
	client, err := goph.New("mpenning", "chestnut.he.net", auth)
	if err != nil {
		logoru.Critical(err.Error())
	}

	logoru.Debug("    Remove old documentation files")
	_, err = client.Run("bash -c 'cd public_html/py/ciscoconfparse/ && rm -rf *'")
	if err != nil {
		logoru.Critical(err.Error())
	}

	logoru.Info("    Start copying doc tarball to remote ssh server")
	err = client.Upload("/home/mpenning/ccp.tar.gz", "public_html/py/ciscoconfparse/ccp.tar.gz")
	if err != nil {
		logoru.Critical(err.Error())
	}
	logoru.Info("    Finished copying tarball to remote ssh server")

	logoru.Info("    extract CiscoConfParse documentation tarball")
	_, err = client.Run("bash -c 'cd public_html/py/ciscoconfparse/ && tar xvfz ./ccp.tar.gz'")
	if err != nil {
		logoru.Critical(err.Error())
	}

	// NOT_NEEDED -> defer client.Close()
}
