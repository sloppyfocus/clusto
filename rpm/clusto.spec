%include %{_rpmconfigdir}/macros.python

# Defaults to --with-mysql unless --without mysql is specified, should this change?
%{!?_without_mysql: %{!?_with_mysql: %define _with_mysql --with-mysql}}
# Defaults to --without-psycopg2
%{!?_with_psycopg2: %{!?_without_psycopg2: %define _without_psycopg2 --without-psycopg2}}

Name:		clusto
Version:	0.7.1
Release:	0%{?dist}
Summary:	Tools and libraries for organizing and managing infrastructure

Group:		Applications/System
License:	BSD
URL:		http://github.com/digg/clusto
Source0:	http://github.com/digg/clusto/tarball/%{name}-%{version}.tar.gz
Patch0:		remove-github-ext-from-sphinx.patch
Patch1:		replace-var-with-libexec.patch
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildArch:	noarch

BuildRequires:	python-devel
BuildRequires:	python-sphinx-doc
%if 0%{?fedora} >= 8
BuildRequires:	python-setuptools-devel
%else
BuildRequires:	python-setuptools
%endif
Requires:	python-sqlalchemy >= 0.5
Requires:	ipython
Requires:	libvirt-python
Requires:   python-IPy
Requires:   scapy >= 2.0
Requires:   PyYAML
%{?_with_mysql:Requires: MySQL-python}
%{?_with_psycopg2:Requires: python-psycopg2}

%description
Clusto is a cluster management tool. It helps you keep track of your inventory,
where it is, how it's connected, and provides an abstracted interface for
interacting with the elements of the infrastructure.


%prep
%setup -q -n %{name}-%{version}
#%patch0 -p1
#%patch1 -p1


%build
%{__python} -c 'import setuptools; execfile("setup.py")' build
# Build documentation
cd doc
make html
rm -f .build/html/.buildinfo


%install
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}
%{__python} -c 'import setuptools; execfile("setup.py")' install -O1 --skip-build --root %{buildroot}
# Create additional directories
mkdir -p %{buildroot}%{_sysconfdir}/%{name}
mkdir -p %{buildroot}%{_libexecdir}/%{name}
cp conf/* %{buildroot}%{_sysconfdir}/%{name}/
cp -R contrib/* %{buildroot}%{_libexecdir}/%{name}/


%clean
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
%doc README LICENSE doc/.build/html
%config(noreplace) %{_sysconfdir}/%{name}
%{py_sitedir}/%{name}*
%attr(0755, root, root) %{_libexecdir}/%{name}/*
%attr(0755, root, root) %{_datadir}/%{name}/*
%attr(0755, root, root) %{_bindir}/*


%changelog
* Tue Mar 26 2013 Jorge A Gallegos <kad@blegh.net> - 0.5.32-5
- add a get_by_ip() method (Mike Newton)
- Don't need add_subparser anymore (Jorge A Gallegos)
- Add clusto-rename command (Jeremy Grosser)
- updating readme to be markdown (Jorge A Gallegos)
- Simplify some things, also eliminate duplicates (Jorge A Gallegos)
- Dropping assert_unicode from schema.py (Jorge A Gallegos)
- You can now override the formatter class (Jorge A Gallegos)
- Fixing clusto-tree to work with current options (Jorge A Gallegos)
- Set the starting namespace for clusto shell (Jorge A Gallegos)
- Virtual servers should only add 2 extra methods (Jorge A Gallegos)
- Added a testGetFromPools test (Jorge A Gallegos)
- schemy.py updates (remove import *s, update DDL events for sqlalchemy >= 0.7); sqlalchemy >= 0.7 now required (Mike Newton)
- add BasicFirewall and BasicLoadBalancer drivers (Mike Newton)
- add Location.insert() instead of using inherited Driver.insert() (Mike Newton)
- Making some minor improvements to captcha function (Jorge A Gallegos)
- r0n noticed i forgot to change netmasks in my tests...oops (Mike Newton)
- update tests for multiple ip bind_ip_to_osport (Mike Newton)
- fix bind_ip_to_osport so ip binds correctly (Mike Newton)
- Removing 2.5 CI (Jorge A Gallegos)
- Adding clusto to travis-ci (Jorge A Gallegos)
- Remove SQLAlchemy version limit, bump to version 0.5.38 (Jeremy Grosser)
- Allow depending on newer IPython (Jeremy Grosser)
- Revert "Rework config and re-introduce clusto.init_script" (Jeremy Grosser)
- Revert "Set SESSION.memcache=None by default" (Jeremy Grosser)
- Set SESSION.memcache=None by default (Jeremy Grosser)
- Rework config and re-introduce clusto.init_script (Jeremy Grosser)
- Cast "number" to an integer (Jeremy Grosser)
- Adding support for IPython >= 0.11 (fixed embedded tabs) (James Downs)
- Adding support for IPython >= 0.11 (James Downs)
- allow list-pool to accept 1-2 pool arguments (Mike Newton)
- Depend on python-pkg-resources (Jeremy Grosser)
- Add clusto initdb (Jeremy Grosser)
- Missing comma in example config... Could've sworn I fixed this before... (Jeremy Grosser)
- Helps if you actually add the files you want... (Jeremy Grosser)
- Update changelog (Jeremy Grosser)
- Add clusto-list-all command (Jeremy Grosser)
- Packaging cleanup, pass lintian (mostly) (Jeremy Grosser)
- Fix maintainer email (Jeremy Grosser)
- arch=all (Jeremy Grosser)
- Packaging updates: add BasicCage, dependency on python-setuptools. (Paul Lathrop)
- Add a BasicCage driver. (Paul Lathrop)
- Update debian/control (Jeremy Grosser)
- fix the debian/copyright license info (Mike Newton)
- Slight mistake on get() (Jorge A Gallegos)
- Split this to https://github.com/clusto/clusto-ec2 (Jorge A Gallegos)
- Somehow this lil' thing got lost (Jorge A Gallegos)
- Writing a setup.py for easy packaging (Jorge A Gallegos)
- Use RawTextHelpFormatter for Paul's pleasure (Jorge Gallegos)
- change load_config() to not require config file (Mike Newton)
- Support importing plugins with CLUSTOPLUGINS environment variable or plugins option in clusto.conf (Jeremy Grosser)
- clusto-shell doesn't work with ipython 0.11 yet (Jorge A Gallegos)
- Re-add dhcp/snmp stuff (Jeremy Grosser)
- Re-integrate clusto-httpd (Jeremy Grosser)
- Pull clusto-httpd back in (Jeremy Grosser)
- Fix clustoec2 README (Jeremy Grosser)
- Re-adding EC2 support in the form of the clustoec2 extension (Jeremy Grosser)
- Move digg drivers into a separate package as an example of how to extend clusto (Jeremy Grosser)
- Make tests pass with no extended drivers (Jeremy Grosser)
- Minimal build of clusto with only core implementations (Jeremy Grosser)
- Updating IP ranges for ec2 (Jorge A Gallegos)
- Boto 2.0 has been released (Jorge A Gallegos)
- Fixing sqlalchemy versioning (Jorge A Gallegos)
- Popular demand: make it easier to write messy code (Jorge A Gallegos)
- A little bit of sugar added to clusto-shell: (Jorge A Gallegos)
- Fixed init_script in commands of the form clusto-* (Jorge A Gallegos)
- A little bit of sugar added to clusto-shell: (Jorge A Gallegos)
- Fixed init_script in commands of the form clusto-* (Jorge A Gallegos)
- Fixing sqlalchemy versioning (Jorge A Gallegos)
- Adding support for tagging/naming instances. (Jorge A Gallegos)
- Raise exception when doing a rollback when no transaction was started. (Ron Gorodetzky)
- clear transaction counter when clearing session (Ron Gorodetzky)
- clean up sql for the common case of querying against the current version (Ron Gorodetzky)
- Raise exception when doing a rollback when no transaction was started. (Ron Gorodetzky)
- clear transaction counter when clearing session (Ron Gorodetzky)
- clean up sql for the common case of querying against the current version (Ron Gorodetzky)
- Fixing sqlalchemy versioning (Jorge A Gallegos)
- sqlalchemy.exceptions are actually sqlalchemy.exc (Jorge A Gallegos)
- sqlalchemy.exceptions are actually sqlalchemy.exc (Jorge A Gallegos)
- Adding EC2IPManager to the ec2 helper (Jorge A Gallegos)
- Updating list of amazon IPs (Jorge A Gallegos)
- Adding EC2IPManager to the ec2 helper (Jorge A Gallegos)
- Updating list of amazon IPs (Jorge A Gallegos)
- Adding support for tagging/naming instances. (Jorge A Gallegos)
- Turns out is not Zip Safe after all (Jorge A Gallegos)
- s/Manger/Manager/ I got you, Ron. Finally. (Jorge A Gallegos)
- * Adde timestamp functionality to do_attr_query (Michael Kania)
- Darnit.  Missed a case where I could end up storing u'None' instead of None. (Lex Linden)
- Eradicated (hopefully) this warning:   SAWarning: Unicode type received non-unicode bind param value (Lex Linden)
- Don't re-raise exceptions; allow existing exception to propagate up so that the caller can more easily debug. (Lex Linden)
- Driver.__new__ should allow any number of arguments to be passed to a subclass's constructor. (Lex Linden)
- Driver.__new__ should not require a name, driver, or entity parameter to be passed.  Let the subclass decide for itself if it wants to require this. (Lex Linden)
- * Have specific exceptions for noninteger port numbers and port numbers less than 1. (Dynamike Linden)
- Really fixing basicrack.py this time (Joshua Tobin)
- Bug fix in basicrack.py (Joshua Tobin)
- Adding functionality to basicrack.py to allow devices other than Device to be inserted into a rack (Joshua Tobin)
- Sorry 'bout that (Jorge A Gallegos)
- Fixing typo in portmixin.py (Joshua Tobin)
- Fuck boilerplate, init_arguments() does all that (Jorge A Gallegos)
- Added missing srcdir variable (Jorge A Gallegos)
- Some cosmetic changes, require sqla >= 0.6.3 (Jorge A Gallegos)
- Ported deallocate (Jorge A Gallegos)
- Added iteration support for Drivers. (Lex Linden)
- Revert simplegeo's changes to static web interface (Jeremy Grosser)
- Remove simplegeo changelog entries (Jeremy Grosser)
- Prepared changelog for build 8 (Simple Geebus)
- Add system.os (Jeremy Grosser)
- Fix http json.loads (Jeremy Grosser)
- Depend on webob for clusto-httpd (Jeremy Grosser)
- Prepared changelog for build 7 (Simple Geebus)
- Install clusto-barker-consumer (Jeremy Grosser)
- Prepared changelog for build 5 (Simple Geebus)
- Set source format (Jeremy Grosser)
- Barker and packaging patches (Jeremy Grosser)
- allow deallocation even if instance already doesn't exist (Ron Gorodetzky)
- change hidden attr escape char to @ (Ron Gorodetzky)
- add an underscore test (Ron Gorodetzky)
- add data to puppet-node2 (Ron Gorodetzky)
- add t1.micro instance type (Ron Gorodetzky)
- update ec2 ip ranges (Ron Gorodetzky)
- fix ec2virtualserver update_metadata to run at least once when wait=False (Ron Gorodetzky)
- add region to userdata template dictionary (Ron Gorodetzky)
- allow ec2virtualserver.update_metadata to wait until state=='running' (Ron Gorodetzky)
- add update_metadata to base Driver (Ron Gorodetzky)
- add ec2 helper to create all ec2 objects (Ron Gorodetzky)
- add basic zone object and EC2Zone driver (Ron Gorodetzky)
- add EC2Region as a datacenter type (Ron Gorodetzky)
- fix locations __init__ files (Ron Gorodetzky)
- let get_or_create take **kwargs (Ron Gorodetzky)
- add clusto-puppet-node2 command (Ron Gorodetzky)
- fix post_*allocation calls (Ron Gorodetzky)
- move EC2IPManager use_ip setup and update_metadata to allocation hooks (Ron Gorodetzky)
- add post_automatic_allocation and post_allocation hooks to ResourceManager (Ron Gorodetzky)
- make get_ip_manager work with any ipmanager type (Ron Gorodetzky)
- fix updating reserved ip list from ec2 and ip allocation (Ron Gorodetzky)
- fix conversion/storage of ip value in ec2ipmanager (Ron Gorodetzky)
- fix ResourceTypeException import (Ron Gorodetzky)
- update ec2ipmanager ip list (Ron Gorodetzky)
- update packaging to depend on boto and mako (Ron Gorodetzky)
- make ec2_user_data a mako template so clusto data (only entity name now) can be replaced (Ron Gorodetzky)
- clear ec2server metadata when deallocating its resources (Ron Gorodetzky)
- add real IP support to ec2virtualserver and initial metadata functions (Ron Gorodetzky)
- if merge_container_attrs is true then attr_value should return the value closest to _this_ thing (Ron Gorodetzky)
- add IPMixin to BasicVirtualServer (Ron Gorodetzky)
- initial implementation of EC2IPManager (Ron Gorodetzky)
- cleanup ipmanager ipy to int conversation (Ron Gorodetzky)
- set number when setting additional_attrs in EC2VMManager (Ron Gorodetzky)
- pass aws auth info when connecting to other regions (Ron Gorodetzky)
- remove difference between default:us-east-1 and us-east-1.  Both will use the default connection. (Ron Gorodetzky)
- add separate additional attrs for ec2 resources for quicker lookups (Ron Gorodetzky)
- add security_group support (Ron Gorodetzky)
- check parents when checking ec2_allow_termination (Ron Gorodetzky)
- make default ec2_region "default:us-east-1" (Ron Gorodetzky)
- add console support for EC2VirtualServer (Ron Gorodetzky)
- handle default us-east-1 region and explicit us-east-1 regions separately (Ron Gorodetzky)
- initial EC2 support with very basic documentation (Ron Gorodetzky)
- remove dependency on BasicServer and BasicVirtualServer from VMManager (Ron Gorodetzky)
- add get_resource_manager method to ResourceManager plus whitespace cleanups (Ron Gorodetzky)
- add support for storing jsonable data (Ron Gorodetzky)
- implement get_by_names (Ron Gorodetzky)
- add docstring to get_by_name (Ron Gorodetzky)
- Add missing dependencies to setup.py (Jeremy Grosser)
- Get rid of annoying XenVirtualServer (Jeremy Grosser)
- clusto-http: Remove non-json responses, fix content types, simplify dumps method (Jeremy Grosser)
- Improve error message for clusto-dancer. (Warren Turkal)
- python-sqlite and python-memcache are not strictly required except to run tests, so make them recommends (Lex Linden)
- Only need python-sqlite (>= 0.6.3), not (>= 0.6.4). (Lex Linden)
- Remove python-sqlalchemy from build-depends.  It's not necessary to build clusto (only to test it). (Lex Linden)
- Added iteration support for Drivers. (Lex Linden)
- Coerce values to be unicode objects (Jorge A Gallegos)
- Finished puppet-node, got rid of digg sauce (Jorge A Gallegos)
- Ported clusto-console, got rid of digg stuff (Jorge A Gallegos)
- Small changes, still trying to figure out things (Jorge A Gallegos)
- I think allocate is mostly done (Jorge A Gallegos)
- Adding assert_driver to get_by_name (Jorge A Gallegos)
- Ported clusto-reboot. Happy birthday to me. (Jorge A Gallegos)
- FAI Defaults to No (Jorge A Gallegos)
- clusto-fai (Jorge A Gallegos)
- Removing unnecessary config parsing (Jorge A Gallegos)
- Add support for get_conf default (Jorge A Gallegos)
- Adding clusto-attr and making setup.py behave (Jorge A Gallegos)
- Adding support to include other files in config (Jorge A Gallegos)
- Adding json and yaml output options (Jorge A Gallegos)
- Adding the list-pool command (Jorge A Gallegos)
- Two changes to script_helper to deal with _ and -: (Jorge A Gallegos)
- Adding the clusto-pool command (Jorge A Gallegos)
- Adding vim swap files to gitignore (Jorge A Gallegos)
- Adding clusto-info script (Jorge A Gallegos)
- Taking advantage of argparse magic (Jorge A Gallegos)

* Wed Jan 19 2011 Jorge A Gallegos <kad@blegh.net> - 0.5.32-4
- add connection cycling (Ron Gorodetzky)
- Fix stupid mistake in spec dates (Jorge A Gallegos)
- clusto-dancer should be in the contrib dir (Jorge A Gallegos)

* Wed Jan 19 2011 Jorge A Gallegos <kad@blegh.net> - 0.5.32-3
- aptitude is stupid (Jorge A Gallegos)

* Tue Oct 19 2010 Jorge A Gallegos <kad@blegh.net> - 0.5.32-2
- The DHCP server now queries the DB directly instead of going thru
  the API
- Fixing the whole suggests/recommends thing
- We need sqlalchemy 0.6.4

* Mon Oct 18 2010 Jorge A Gallegos <kad@blegh.net> - 0.5.32-1
- 755 (Jorge Gallegos)
- Adding ability to pass a default argument to the config getter
  (Jorge Gallegos)
- keep del_attrs from removing hidden attrs by default (Ron
  Gorodetzky)
- initial feature complete version (William Francis)
- new clusto-mysql script (William Francis)

* Thu Sep 30 2010 Jorge A Gallegos <kad@blegh.net> - 0.5.31-6
- Adding the web interface to the package (Jorge A Gallegos)

* Mon Sep 27 2010 Jorge A Gallegos <kad@blegh.net> - 0.5.31-5
- JS runs on the client... (Jorge A Gallegos)

* Mon Sep 27 2010 Jorge A Gallegos <kad@blegh.net> - 0.5.31-4
- I broke get_entities. I fixed get_entities. (Jorge A Gallegos)

* Wed Sep 22 2010 Jorge A Gallegos <kad@blegh.net> - 0.5.31-3
- Some unicode fixes (Jorge A Gallegos)

* Mon Sep 20 2010 Jorge A Gallegos <kad@blegh.net> - 0.5.31-2
- Fixing a stupid bug (Jorge A Gallegos)
- Adding clusto-orphans script (Jorge A Gallegos)

* Thu Sep 16 2010 Jorge A Gallegos <kad@blegh.net> - 0.5.31-1
- Initial memcache support

* Mon Jul 12 2010 Jorge A Gallegos <kad@blegh.net> - 0.5.29-2
- Fixed %files section

* Mon Jun 28 2010 Jorge A Gallegos <kad@blegh.net> - 0.5.29-1
- add tests for reserving resources
- Adding 'deallocate' command
- Patched list-pool so it doesn't barf when the content is a pool (or
  any other object with no get_ips() method)

* Sat May 8 2010 Jorge A Gallegos <kad@blegh.net> - 0.5.27-3
- Use standard python macros

* Thu May 6 2010 Jeremy Grosser <synack@digg.com> - 0.5.27-2
- Fixed make_tarball.sh script

* Wed May 5 2010 Jeremy Grosser <synack@digg.com> - 0.5.27-1
- Version bump

* Wed May 5 2010 Jorge A Gallegos <kad@blegh.net> - 0.5.26-4
- Adding python-IPy dependency

* Wed May 5 2010 Jorge A Gallegos <kad@blegh.net> - 0.5.26-3
- Packager should go in ~/.rpmmacros

* Tue May 4 2010 Jorge A Gallegos <kad@blegh.net> - 0.5.26-2
- Moved contrib from /var/lib/clusto to /usr/libexec/clusto
- Added sysconf directory defaults
- Added scapy dependency
- Added libvirt-python dependency
- Added mysql conditional dependency (defaults to --with)
- Added psycopg2 conditional dependency (defaults to --without)

* Tue May 4 2010 Jorge A Gallegos <kad@blegh.net> - 0.5.26-1
- First spec draft

