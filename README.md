# The Rockstor Project

An Open Source (Licensed: FSF Free/Libre & OSI approved) community endeavour
to sustainably develop, maintain, and distribute an easy to use, flexible,
Linux & BTRFS based DIY Network Attached Storage (NAS) software appliance.

[About Us](https://rockstor.com/about-us.html)

# License:

The Rockstor package code, as distributed, is developed under two main repositories:

* Source0: [rockstor-core](https://github.com/rockstor/rockstor-core) is
  [GPL-3.0-or-later](https://www.gnu.org/licenses/gpl-3.0-standalone.html) licensed.

* Source1: [rockstor-jslibs](https://github.com/rockstor/rockstor-jslibs) is
  ([MIT](https://opensource.org/license/mit-0) AND
  [Apache-2.0](https://opensource.org/license/apache2.0) AND
  [GPL-3.0-or-later](https://www.gnu.org/licenses/gpl-3.0-standalone.html) AND
  [LGPL-3.0-or-later](https://www.gnu.org/licenses/lgpl-3.0-standalone.html) AND
  [ISC](https://spdx.org/licenses/ISC.html)) licensed.
  Indicating the combined works in this jslibs repository.

Making the package license, as per the **Fedora Project Wiki**
[Packaging:LicensingGuidelines](https://fedoraproject.org/wiki/Packaging:LicensingGuidelines#Mixed_Source_Licensing_Scenario):

* **"GPL-3.0-or-later AND (MIT AND Apache-2.0 AND GPL-3.0-or-later AND LGPL-3.0-or-later AND ISC)"**

The optional [Rock-ons (Docker Plugins)](https://rockstor.com/docs/interface/overview.html)
sub-system uses definitions developed in the 
[rockon-registry](https://github.com/rockstor/rockon-registry) which are
licensed [AGPL-3.0-or-later](https://spdx.org/licenses/AGPL-3.0-or-later.html).
These definitions are not included within our distributed package,
but retrieved via the internet (from production servers) upon this sub-systems setup.

*Note: All additional software installed via the optional Rock-on sub-system
is subject to the individual projects licensing terms.
As indicated by their respective websites: linked within Rockstors Rock-ons Web-UI.*

See the [SPDX License List](https://spdx.org/licenses) for details on the above assertions.

# Documentation

[Our Documentation](https://rockstor.com/docs) is developed in the open in the
[rockstor-doc](https://github.com/rockstor/rockstor-doc) repository and
licensed [CC-BY-SA-4.0](https://creativecommons.org/licenses/by-sa/4.0).
As with all our code, contributions and corrections are always welcome.

# What is Rockstor?

Rockstor is a Network Attached Storage (NAS) solution built on Linux and the B-Tree
Filesystem (BTRFS). It is written in Python and Javascript and is made
available as a complete Linux distribution for convenience. Rockstor takes NAS
to a new level with advanced features, ease of use, and management. It goes
beyond traditional NAS by supporting Docker based apps, RESTful APIs; and serves as a
private cloud storage platform out-of-the-box.

# What are the project goals?

The main goal is to establish sustainable Open Source development
of an easy to deploy and use NAS solution for commodity hardware.
For more information, see:
[Our Endeavour](https://rockstor.com/about-us.html).

# Who should use it?

The Rockstor Project aims to aid individuals and organisations alike.
As a DIY appliance some familiarity with PC/Pi4/ARM64 operating system install is required;
but not much beyond the basics.
For more information see our main website:
[rockstor.com](https://rockstor.com)

# Getting started and questions

The best way to get started is by following the [quickstart
guide](https://rockstor.com/docs/quickstart.html).

To get in touch with developers, users, and contributors join our
[community forum](https://forum.rockstor.com) and ask away.


# Troubleshooting

The [community forum](https://forum.rockstor.com) is the ideal location for help and 
support; all current developers are also active forum members.

# Issue tracking

We use GitHubs issues, although a forum post/discussion is advised beforehand.
This often helps with clarifying exactly what any new issue should contain;
or in establishing if any existing issue is relevant.
It is also important to correctly identify the relevant
[rockstor](https://github.com/rockstor) repository.

# Contributing

Development environment setup and contribution guidelines are available in our docs:
[Contributing to Rockstor - Overview](https://rockstor.com/docs/contribute/contribute.html)

There is no Contributor License Agreement (CLA).

Pull requests are welcome. Pick an issue that interests you or create a new one.
Reference our [friendly community forum ](https://forum.rockstor.com)
for open questions and our ever-growing wiki entries that serve as our
community facing developer notes.  
