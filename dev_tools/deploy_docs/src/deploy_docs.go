package deploy_docs

import (
	// logoru is for colored logging...
	"github.com/gleich/logoru"
	// golorama is for colored printing...

	// go-pretty is for colored text tables...

	// goph is for ssh automation...
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/melbahja/goph"
)

func localizedTime(timespec string, tzlocation string) string {

	// localize a Location to a standard timestring like
	// 'UTC', 'Local', 'Pacific', or 'US/Chicago'
	tzLoc, err := time.LoadLocation(tzlocation)
	if err != nil {
		logoru.Error(err.Error())
	}

	if strings.ToLower(timespec) == "now" {
		timestamp := time.Now().In(tzLoc)
	} else {

		// 2023-09-15 09:04:03
		dateRe := regexp.MustCompile(`^(<year>?P\d{4})-(<month>?P\d{2})-(<day>?P\d{2})\s+(<hour>?P\d{2}):(<minute>?P\d{2}):(<second>?P\d{2})$`)
		dateRe_matches := dateRe.FindStringSubmatch(timespec)
		// build the indexes into dateRe_matches...
		yearIndex := dateRe.SubexpIndex("year")
		monthIndex := dateRe.SubexpIndex("month")
		dayIndex := dateRe.SubexpIndex("day")
		hourIndex := dateRe.SubexpIndex("hour")
		minuteIndex := dateRe.SubexpIndex("minute")
		secondIndex := dateRe.SubexpIndex("second")
		// build the integer values...
		year, err := strconv.ParseInt(dateRe_matches[yearIndex], 10, 64)
		if err != nil {
			logoru.Critical(err.Error())
		}
		month, err := strconv.ParseInt(dateRe_matches[monthIndex], 10, 64)
		if err != nil {
			logoru.Critical(err.Error())
		}
		day, err := strconv.ParseInt(dateRe_matches[dayIndex], 10, 64)
		if err != nil {
			logoru.Critical(err.Error())
		}
		hour, err := strconv.ParseInt(dateRe_matches[hourIndex], 10, 64)
		if err != nil {
			logoru.Critical(err.Error())
		}
		minute, err := strconv.ParseInt(dateRe_matches[minuteIndex], 10, 64)
		if err != nil {
			logoru.Critical(err.Error())
		}
		second, err := strconv.ParseInt(dateRe_matches[secondIndex], 10, 64)
		if err != nil {
			logoru.Critical(err.Error())
		}

		// timestamp from the timespec string...
		timestamp := time.Date(year, month, day, hour, minute, second).In(tzLoc)
	}

	return timestamp

}

func main() {

	logoru.Info("Starting CiscoConfParse new documentation build and upload")

	tzLoc_UTC, err := time.LoadLocation("UTC")
	if err != nil {
		logoru.Critical(err.Error())
	}
	tzLoc_Local, _ := time.LoadLocation("Local")
	if err != nil {
		logoru.Critical(err.Error())
	}

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
