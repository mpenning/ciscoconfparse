package main

import (
	"flag"

	// goph is an ssh client...
	"github.com/melbahja/goph"

	// zap provides useful logging...
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

// Declare all variables here...
var (
	dochost string = ""
)

func main() {

	logconfig := zap.NewDevelopmentConfig()
	logconfig.EncoderConfig.EncodeLevel = zapcore.CapitalColorLevelEncoder
	logger, _ := logconfig.Build()

	// define CLI flags here... '--dochost' is saved as string variable -> dochost
	flag.StringVar(&dochost, "dochost", "127.0.0.1", "host to upload docs to.")
	flag.Parse()

	//logger.Info("Starting CiscoConfParse new documentation upload to " + fmt.Sprintf("%s", dochost) + ".")
	logger.Info("Starting CiscoConfParse new documentation upload to " + dochost + ".")

	// Start a new goph ssh connection with private key auth...
	logger.Info("    Initialize ssh key-auth")
	auth, err := goph.Key("/home/mpenning/.ssh/id_ed25519", "")
	if err != nil {
		logger.Fatal(err.Error())
	}

	// Get an ssh client instance with private-key / public-key auth...
	logger.Info("    ssh into remote webhost " + dochost + ".")
	client, err := goph.New("mpenning", dochost, auth)
	if err != nil {
		logger.Fatal(err.Error())
	}

	// Run a shell command via the 'client' ssh connection to dochost...
	logger.Info("    Remove old documentation files")
	_, err = client.Run("bash -c 'cd public_html/py/ciscoconfparse/ && rm -rf *'")
	if err != nil {
		logger.Fatal(err.Error())
	}

	// Upload a file to the remote server...
	logger.Info("    Start copying doc tarball to remote ssh server")
	err = client.Upload("/home/mpenning/ccp.tar.gz", "public_html/py/ciscoconfparse/ccp.tar.gz")
	if err != nil {
		logger.Fatal(err.Error())
	}
	logger.Info("    Finished copying tarball to remote ssh server")

	logger.Info("    extract CiscoConfParse documentation tarball")
	_, err = client.Run("bash -c 'cd public_html/py/ciscoconfparse/ && tar xvfz ./ccp.tar.gz'")
	if err != nil {
		logger.Fatal(err.Error())
	}

	// NOT_NEEDED -> defer client.Close()
}
