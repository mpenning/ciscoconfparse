package main

import (
	"os"
	"time"

	"github.com/melbahja/goph"
	"github.com/urfave/cli/v2"

	// zap provides useful logging...
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

func buildAppInstance(logger *zap.Logger) (appInst *cli.App) {

	var dochost string = ""

	appInst = &cli.App{
		Name:     "deploy_docs",
		Version:  "0.0.2",
		Compiled: time.Now(),
		Authors: []*cli.Author{
			&cli.Author{
				Name:  "Mike Pennington",
				Email: "mike@pennington.net",
			},
		},
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:        "dochost",
				Value:       "127.0.0.1",
				Usage:       "FQDN or IPv4 of the documentation host",
				Destination: &dochost,
			},
		},
		Action: func(cCtx *cli.Context) (err error) {
			logger.Info("Starting cli.Context action")
			if cCtx.NArg() == 0 {
				logger.Fatal("No CLI arguments detected!")
			}
			return nil
		},
	}
	if dochost == "" {
		logger.Debug("'dochost' is an empty string!")
		os.Exit(1)
	}
	return appInst

}

func main() {

	logconfig := zap.NewDevelopmentConfig()
	logconfig.EncoderConfig.EncodeLevel = zapcore.CapitalColorLevelEncoder
	logger, _ := logconfig.Build()

	logger.Info("Starting CiscoConfParse new documentation upload")
	app := buildAppInstance(logger)
	app = app

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
