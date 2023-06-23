package main

import (
	"github.com/melbahja/goph"
	// zap provides useful logging...
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

func main() {

	logconfig := zap.NewDevelopmentConfig()
	logconfig.EncoderConfig.EncodeLevel = zapcore.CapitalColorLevelEncoder
	logger, _ := logconfig.Build()

	logger.Info("Starting CiscoConfParse new documentation upload")

	logger.Info("    Initialize ssh key-auth")
	// Start new ssh connection with private key.
	auth, err := goph.Key("/home/mpenning/.ssh/id_ed25519", "")
	if err != nil {
		logger.Fatal(err.Error())
	}

	logger.Info("    ssh into remote webhost")
	client, err := goph.New("mpenning", "chestnut.he.net", auth)
	if err != nil {
		logger.Fatal(err.Error())
	}

	logger.Info("    Remove old documentation files")
	_, err = client.Run("bash -c 'cd public_html/py/ciscoconfparse/ && rm -rf *'")
	if err != nil {
		logger.Fatal(err.Error())
	}

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
