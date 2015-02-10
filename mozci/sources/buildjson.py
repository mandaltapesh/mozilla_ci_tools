#!/usr/bin/env python
"""
This module helps with the buildjson data generated by the Release Engineering
systems: http://builddata.pub.build.mozilla.org/builddata/buildjson
"""
import datetime
import json
import logging
import os
import requests

LOG = logging.getLogger()

BUILDJSON_DATA = "http://builddata.pub.build.mozilla.org/builddata/buildjson"


def _fetch_buildjson_day_file(date):
    '''
       In BUILDJSON_DATA we have the information about all jobs stored
       as a gzip file per day.

       This function caches the uncompressed gzip files requested in the past.

       This function returns a json object containing all jobs for a given day.

       # XXX: The day's file for today is always generated every 15 minutes
       We should not grab information for jobs that were scheduled today more than
       for 4 hours ago through this function.
    '''
    data_file = "builds-%s.js" % date

    if not os.path.exists(data_file):
        url = "%s/%s.gz" % (BUILDJSON_DATA, data_file)
        LOG.debug("We have not been able to find on disk %s." % data_file)
        LOG.debug("We will now fetch %s" % url)
        # Fetch tar ball
        req = requests.get(url)
        # NOTE: requests deals with decrompressing the gzip file
        with open(data_file, 'wb') as fd:
            for chunk in req.iter_content(chunk_size=1024):
                fd.write(chunk)

    return json.load(open(data_file))["builds"]


def _fetch_buildjson_4hour_file():
    '''
    This file is generate every minute.
    It has the same data as today's buildjson day file but only for the
    last 4 hours.
    '''
    raise Exception("We have not yet implemented the feature")


def query_job_data(claimed_at, request_id):
    """
    This function looks for a job identified by `request_id` inside of a
    buildjson file under the "builds" entry.

    Through `claimed_at`, we can determine on which day we can find the
    metadata about this job.

    If found, the returning entry will look like this (only important values
    are referenced):
    {
        "builder_id": int, # It is a unique identifier of a builder
        "starttime": int,
        "endtime": int,
        "properties": {
            "buildername": string,
            "buildid": string,
            "revision": string,
            "repo_path": string, # e.g. projects/cedar
            "log_url", string,
            "slavename": string, # e.g. t-w864-ix-120
            "blobber_files": json, # Mainly applicable to test jobs
            "packageUrl": string, # It only applies for build jobs
            "testsUrl": string,   # It only applies for build jobs
            "symbolsUrl": string, # It only applies for build jobs
        },
        "request_ids": list of ints, # Scheduling ID
        "requestime": int,
        "result": int, # Job's exit code
        "slave_id": int, # Unique identifier for the machine that run it
    }
    """
    assert type(request_id) is int
    assert type(claimed_at) is int

    date = datetime.datetime.fromtimestamp(claimed_at).strftime('%Y-%m-%d')
    LOG.debug("Job identified with claimed_at value: %d run on %s" % (claimed_at, date))

    if datetime.date.today() == date:
        # XXX: We should really check if it is more than 4 hours
        builds = _fetch_buildjson_4hour_file(date)
    else:
        builds = _fetch_buildjson_day_file(date)

    LOG.debug("We are going to look for %s through the jobs run on %s." %
              (request_id, date))
    for job in builds:
        if request_id in job["request_ids"]:
            LOG.debug("Found %s" % str(job))
            return job
