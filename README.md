# openCARP CI

This package contains a set of Python scripts, which can be used to perform tasks around the archival and long term preservation of software repositories. In particular, it can be used to:

* create a release in GitLab using the GitLab API,
* create a DataCite record based on different YAML files present in the repository,
* create archive packages in the [BagIt](https://tools.ietf.org/html/rfc8493) or [BagPack](https://www.rd-alliance.org/system/files/Research%20Data%20Repository%20Interoperability%20WG%20-%20Final%20Recommendations_reviewed_0.pdf) format.
* archive the software using the [RADAR service](https://www.radar-service.eu),
* use content from markdown files, bibtex files, or python docstrings to create web pages in a [Grav CMS](https://getgrav.org/).

The scripts where created for the [openCARP](https://opencarp.org) simulation software, but can be adopted for arbitray projects. While they can be used on the command line, the scripts are mainly used with the GitLab CI to run automatically run on each push to a repository, or when a tag is created.


## Setup

To use the scripts whithin the GitLab CI, add the following to your job:

```yaml
  before_script:
  - pip install git+https://git.opencarp.org/openCARP/openCARP-CI
```

In order to run the scripts on the command line, we recomment to use a [virtual environment](https://docs.python.org/3/library/venv.html):

```bash
python -m venv env
source env/bin/activate
pip install git+https://git.opencarp.org/openCARP/openCARP-CI
```


## Usage

Each of the scripts expects a number of command line arguments. Default values can be set using enviroment variables (using upper case and underscores), i.e. the following lines do the same:

```bash
create_bag --bag-path=/path/to/bag
BAG_PATH=/path/to/bag create_bag
```

Enviroments variables can be set in the usual way, e.g. the `.gitlab-ci.yml` file, but also in a `.env` file in the directory where the script is invoked. See `.env.sample` for a sample environment file.


The following scripts are included:


### create_release

Creates a release in GitLab using the GitLab API. A tag for the release needs to be created before and provided to the script.

```
usage: create_release [-h] [--release-tag RELEASE_TAG]
                      [--release-description RELEASE_DESCRIPTION]
                      [--release-api-url RELEASE_API_URL] [--private-token PRIVATE_TOKEN]
                      [--dry] [--log-level LOG_LEVEL] [--log-file LOG_FILE]
                      [assets [assets ...]]

positional arguments:
  assets                Assets to be included in the release.

optional arguments:
  -h, --help            show this help message and exit
  --release-tag RELEASE_TAG
                        Tag for the release.
  --release-description RELEASE_DESCRIPTION
                        Description for the release.
  --release-api-url RELEASE_API_URL
                        API URL to create the release.
  --private-token PRIVATE_TOKEN
                        The PRIVATE_TOKEN to be used with the GitLab API.
  --dry                 Perform a dry run, do not perfrom the final request.
  --log-level LOG_LEVEL
                        Log level (ERROR, WARN, INFO, or DEBUG)
  --log-file LOG_FILE   Path to the log file
```

### create_datacite

Creates a DataCite XML file following the [DataCite Metadata Schema 4.3](https://schema.datacite.org/meta/kernel-4.3/). The information needed for this can be taken from (a list) of locations given as URL or local file path. `METADATA_LOCATIONS` must point to YAML files following an adaptation of [DataCite JSON](https://github.com/datacite/schema/tree/master/source/json/kernel-4.3). `CREATORS_LOCATIONS` and `CONTRIBUTORS_LOCATIONS` point to similar files which contain a list of `creators` or `contributors`, repectively.

For examples, see https://git.opencarp.org/openCARP/openCARP/blob/master/METADATA.yml and https://git.opencarp.org/openCARP/openCARP/blob/master/CONTRIBUTORS.yml.

```
usage: create_datacite [-h] [--metadata-location METADATA_LOCATIONS]
                       [--creators-location CREATORS_LOCATIONS]
                       [--contributors-location CONTRIBUTORS_LOCATIONS] [--version VERSION]
                       [--issued ISSUED] [--datacite-path DATACITE_PATH]
                       [--log-level LOG_LEVEL] [--log-file LOG_FILE]

optional arguments:
  -h, --help            show this help message and exit
  --metadata-location METADATA_LOCATIONS
                        Locations of the metadata YAML files
  --creators-location CREATORS_LOCATIONS
                        Locations of the creators YAML files
  --contributors-location CONTRIBUTORS_LOCATIONS
                        Locations of the contributors YAML files
  --version VERSION     Version of the resource
  --issued ISSUED       Date for the Issued field and publication year (format: '%Y-%m-%d')
  --datacite-path DATACITE_PATH
                        Path to the DataCite XML output file
  --log-level LOG_LEVEL
                        Log level (ERROR, WARN, INFO, or DEBUG)
  --log-file LOG_FILE   Path to the log file
```

### create_bag

Creates a bag [BagIt](https://tools.ietf.org/html/rfc8493) using the [bagit-python](https://github.com/LibraryOfCongress/bagit-python) package. The assets to be included in the bag are given as positional arguments.

```
usage: create_bag [-h] [--bag-path BAG_PATH] [--bag-info-location BAG_INFO_LOCATIONS]
                  [--log-level LOG_LEVEL] [--log-file LOG_FILE]
                  [assets [assets ...]]

positional arguments:
  assets                Assets to be added to the bag.

optional arguments:
  -h, --help            show this help message and exit
  --bag-path BAG_PATH   Path to the Bag directory
  --bag-info-location BAG_INFO_LOCATIONS
                        Locations of the bog-info YAML files
  --log-level LOG_LEVEL
                        Log level (ERROR, WARN, INFO, or DEBUG)
  --log-file LOG_FILE   Path to the log file
```

### create_bagpack

Creates a bag [BagIt](https://tools.ietf.org/html/rfc8493) similar to `create_bag.py`, but also includes a DataCite XML file as recomended by the [RDA Research Data Repository Interoperability WG](https://www.rd-alliance.org/system/files/Research%20Data%20Repository%20Interoperability%20WG%20-%20Final%20Recommendations_reviewed_0.pdf).

```
usage: create_bagpack [-h] [--bag-path BAG_PATH] [--bag-info-location BAG_INFO_LOCATIONS]
                      [--datacite-path DATACITE_PATH] [--log-level LOG_LEVEL]
                      [--log-file LOG_FILE]
                      [assets [assets ...]]

positional arguments:
  assets                Assets to be added to the bag.

optional arguments:
  -h, --help            show this help message and exit
  --bag-path BAG_PATH   Path to the Bag directory
  --bag-info-location BAG_INFO_LOCATIONS
                        Locations of the bog-info YAML files
  --datacite-path DATACITE_PATH
                        Path to the DataCite XML file
  --log-level LOG_LEVEL
                        Log level (ERROR, WARN, INFO, or DEBUG)
  --log-file LOG_FILE   Path to the log file
```

### create_radar

Creates an archive in the [RADAR service](https://www.radar-service.eu) and upload the assets provided as positional arguments. The metadata is created similar to `create_datacite`.

```
usage: create_radar [-h] [--metadata-location METADATA_LOCATIONS]
                    [--creators-location CREATORS_LOCATIONS]
                    [--contributors-location CONTRIBUTORS_LOCATIONS] [--version VERSION]
                    [--issued ISSUED] [--radar-path RADAR_PATH] [--radar-url RADAR_URL]
                    [--radar-username RADAR_USERNAME] [--radar-password RADAR_PASSWORD]
                    [--radar-client-id RADAR_CLIENT_ID]
                    [--radar-client-secret RADAR_CLIENT_SECRET]
                    [--radar-contract-id RADAR_CONTRACT_ID]
                    [--radar-workspace-id RADAR_WORKSPACE_ID]
                    [--radar-redirect-url RADAR_REDIRECT_URL] [--radar-email RADAR_EMAIL]
                    [--radar-backlink RADAR_BACKLINK] [--dry] [--log-level LOG_LEVEL]
                    [--log-file LOG_FILE]
                    [assets [assets ...]]

positional arguments:
  assets                Assets to be added to the repository.

optional arguments:
  -h, --help            show this help message and exit
  --metadata-location METADATA_LOCATIONS
                        Locations of the metadata YAML files
  --creators-location CREATORS_LOCATIONS
                        Locations of the creators YAML files
  --contributors-location CONTRIBUTORS_LOCATIONS
                        Locations of the contributors YAML files
  --version VERSION     Version of the resource
  --issued ISSUED       Date for the Issued field and publication year (format: '%Y-%m-%d')
  --radar-path RADAR_PATH
                        Path to the Radar directory, where the assets are collected before
                        upload.
  --radar-url RADAR_URL
                        URL of the RADAR service.
  --radar-username RADAR_USERNAME
                        Username for the RADAR service.
  --radar-password RADAR_PASSWORD
                        Password for the RADAR service.
  --radar-client-id RADAR_CLIENT_ID
                        Client ID for the RADAR service.
  --radar-client-secret RADAR_CLIENT_SECRET
                        Client secret for the RADAR service.
  --radar-contract-id RADAR_CONTRACT_ID
                        Contract ID for the RADAR service.
  --radar-workspace-id RADAR_WORKSPACE_ID
                        Workspace ID for the RADAR service.
  --radar-redirect-url RADAR_REDIRECT_URL
                        Redirect URL for the OAuth workflow of the RADAR service.
  --radar-email RADAR_EMAIL
                        Email for the RADAR metadata.
  --radar-backlink RADAR_BACKLINK
                        Backlink for the RADAR metadata.
  --dry                 Perform a dry run, do not upload anything.
  --log-level LOG_LEVEL
                        Log level (ERROR, WARN, INFO, or DEBUG)
  --log-file LOG_FILE   Path to the log file
```

### run_markdown_pipeline

Copies the content of markdown files in the `PIPELINE_SOURCE` to a Grav CMS repository given by `GRAV_PATH`. The Grav repository is created by the [Git-Sync Plugin](https://getgrav.org/blog/git-sync-plugin).

The pages need to be already existing in Grav and contain a `pipeline` and a `source` field in their frontmatter. The script will find all pages which match the provided `PIPELINE` and will overwrite content part of the page with the markdown file given by `source`.

After running the script, the changes to the Grav CMS repository can be committed and pushed and the Git-Sync Plugin will update the public pages.

```
usage: run_markdown_pipeline [-h] [--grav-path GRAV_PATH] [--pipeline PIPELINE]
                             [--pipeline-source PIPELINE_SOURCE] [--log-level LOG_LEVEL]
                             [--log-file LOG_FILE]

optional arguments:
  -h, --help            show this help message and exit
  --grav-path GRAV_PATH
                        Path to the grav repository directory.
  --pipeline PIPELINE   Name of the pipeline as specified in the GRAV metadata.
  --pipeline-source PIPELINE_SOURCE
                        Path to the source directory for the pipeline.
  --log-level LOG_LEVEL
                        Log level (ERROR, WARN, INFO, or DEBUG)
  --log-file LOG_FILE   Path to the log file
```

### run_bibtex_pipeline

Compiles and copies the content of bibtex files in a similar way to `run_markdown_pipeline`. A [CSL](https://citationstyles.org/) can be provided.

```
usage: run_bibtex_pipeline [-h] [--grav-path GRAV_PATH] [--pipeline PIPELINE]
                           [--pipeline-source PIPELINE_SOURCE]
                           [--pipeline-csl PIPELINE_CSL]
                           [--log-level LOG_LEVEL] [--log-file LOG_FILE]

optional arguments:
  -h, --help            show this help message and exit
  --grav-path GRAV_PATH
                        Path to the grav repository directory.
  --pipeline PIPELINE   Name of the pipeline as specified in the GRAV
                        metadata.
  --pipeline-source PIPELINE_SOURCE
                        Path to the source directory for the pipeline.
  --pipeline-csl PIPELINE_CSL
                        Path to the source directory for the pipeline.
  --log-level LOG_LEVEL
                        Log level (ERROR, WARN, INFO, or DEBUG)
  --log-file LOG_FILE   Path to the log file
```
