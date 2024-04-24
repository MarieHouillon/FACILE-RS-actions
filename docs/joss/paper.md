---
title: 'FACILE-RS: archival and long term preservation of research software repositories made easy'
tags:
  - Python
  - FAIR
  - Research Software
authors:
  - given-names: Jochen
    surname: Klar
    orcid: 0000-0002-5883-4273
    affiliation: 1
  - given-names: Marie
    surname: Houillon
    orcid: 0000-0002-6584-0233
    affiliation: 2
  - given-names: Axel
    surname: Loewe
    orcid: 0000-0002-2487-4744
    affiliation: 2
  - given-names: Ziad
    surname: Boutanios
    affiliation: 2
  - given-names: Tomas
    surname: Stary
    orcid: 0000-0001-9614-6263
    affiliation: 2
affiliations:
 - name: Independent Software Developer, Germany
   index: 1
 - name: Karlsruhe Institute of Technology, Germany
   index: 2
date: 24 April 2024
bibliography: paper.bib
---

<!-- From the directory containing this file, you can build paper.pdf using Docker:
docker run --rm \
    --volume $PWD:/data \
    --user $(id -u):$(id -g) \
    --env JOURNAL=joss \
    openjournals/inara
 -->

# Summary

The FACILE-RS Python package allows to perform tasks around the archival and long term preservation of research software repositories. It consists in a set of Python scripts which facilitate the maintenance of software metadata by automating the generation of metadata in various formats from a unique metadata file that is maintained manually. FACILE-RS also makes it easier to publish and archive software releases according to the Open Science paradigm and the FAIR (Findable, Accessible, Interoperable, Reusable) principles for Research Software, by offering tools to automate the creation of releases and the upload to persistent research data repositories.

In particular, FACILE-RS allows to:

* create a [DataCite](http://schema.datacite.org/) record based on [CodeMeta](https://codemeta.github.io/) files present in repositories,
* create a [CFF (Citation File Format) file](https://citation-file-format.github.io) from CodeMeta files,
* create archive packages in the [BagIt](https://tools.ietf.org/html/rfc8493) or [BagPack](https://www.rd-alliance.org/system/files/Research%20Data%20Repository%20Interoperability%20WG%20-%20Final%20Recommendations_reviewed_0.pdf) formats,
* create a release on the Develpment platform GitLab using the GitLab API,
* archive software releases using the [RADAR service](https://www.radar-service.eu),
* use content from markdown files, bibtex files, or python docstrings to create web pages within the [Grav CMS](https://getgrav.org/).

While the scripts can be run manually, they are designed to be used within [GitLab CI/CD](https://docs.gitlab.com/ee/ci/) or another workflow automation system, in order to automate the process of maintaining metadata and creating persistent software releases.


# Statement of need

Research software development is a fundamental aspect of academic research [@anzt2021sustainable],
and it has now been acknowledged that the FAIR principles (Findable, Accessible, Interoperable,
Reusable; [@wilkinson2016fair]), historically established to improve the reusability of research data, should
also be applied to research software [@ChueHong2021FAIR]. In particular, reproducible
research requires that software and their associated metadata can be found easily by both
machines and humans, and that they are retrievable via standardised protocols. In this
context, several metadata standards are widely used across the scientific community:

- the Citation File Format (CFF) [@Druskat2021CFF] aims to indicate to users how to cite a software package,
- DataCite [@DataCite2021] is a standard Metadata schema for archiving digital assets,
- CodeMeta [@jones2017codemeta] is an extension of schema.org created to standardize
the exchange of software metadata across repositories and organizations.

All of these standards serve specific purposes and several of them are required to cover
the whole software lifecycle. However, maintaining multiple metadata files in different formats represents a burden for research software developers, and can prevent them from adopting good software publication practices. In addition, as the content of the different metadata files is largely overlapping, maintaining these files manually can pose a risk to data consistency.

<!-- Maybe: add something about the fact that each software version should be released according to the FAIR principles and assigned a persistent identifier, and that this is laborious to do if no streamlined process exists. -->

FACILE-RS aims to overcome these difficulties by making it easy to create and maintain the metadata associated to research software, as well as to publish software releases according to the FAIR principles on reputable research data repositories.


# Functionality

The main prerequisite for using FACILE-RS in a software repository is to create a CodeMeta metadata file, for example using the [CodeMeta generator](https://codemeta.github.io/codemeta-generator/). This metadata format is specifically tailored for describing scientific software.

The Python scripts that compose FACILE-RS are gathered in \autoref{tab:cluster}. While each of these scripts can be used individually and run manually, FACILE-RS was designed to be used within an automated workflow, for example using [GitLab CI/CD](https://about.gitlab.com/topics/ci-cd/), a tool for automating software development workflows via a continuous and iterative process. 

\begin{table}[!ht]
\vspace{5mm}
\centering
\begin{tabular}{ll}
\hline
Script & Functionality \\
\hline\hline
\texttt{create\_cff}              & generates Citation File Format (CFF) metadata file \\
\texttt{prepare\_release}         & updates \textit{version} and \textit{dateModified} fields in metadata \\
\texttt{create\_release}          & creates release in GitLab \\
\texttt{create\_datacite}         & generates DataCite metadata file \\
\texttt{create\_bag}              & creates BagIt package \\
\texttt{create\_bagpack}          & adds DataCite XML to BagIt package \\
\texttt{prepare\_radar}           & reserves DOI on RADAR \\
\texttt{create\_radar}            & creates archive and uploads it to RADAR\\
\texttt{run\_markdown\_pipeline}  & updates Grav CMS website \\
\texttt{run\_bibtex\_pipeline}    & converts BibTex files and publishes references on \\
 & Grav CMS website \\
\texttt{run\_docstring\_pipeline} & extracts docstrings from Python scripts and publishes \\
 & them on Grav CMS website \\
\hline
\end{tabular}
\caption{\small Components of FACILE-RS}\label{tab:cluster}
\end{table}

A typical FACILE-RS workflow in GitLab CI/CD is illustrated on figure \autoref{fig:facile-rs-workflow}. In this example, each time a commit is published, the different metadata files are automatically updated from the CodeMeta file.

This workflow also includes an automated process for creating software releases, both on GitLab and on the research repository RADAR.
This process is triggered by creating a _pre-release_ tag, which would be `pre-v0.1.0` for creating the release of version `v0.1.0`.
During the _pre-release_ phase, a DOI is reserved on RADAR and the software metadata associated with the release is updated. Once this is done, the proper release tag is automatically created, and the GitLab and RADAR releases are created.

[Several tutorials](https://git.opencarp.org/openCARP/FACILE-RS/-/tree/master/docs/tutorials?ref_type=heads) for implementing such a workflow are provided within the FACILE-RS repository.

![Typical structure of an automated FACILE-RS workflow\label{fig:facile-rs-workflow}](images/facile-rs-workflow.png){ width=95% }


# Acknowledgements

We acknowledge ...

# References