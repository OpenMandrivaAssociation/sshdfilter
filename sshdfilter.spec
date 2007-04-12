%define name	sshdfilter
%define version	1.4.5
%define release	%mkrel 1

Summary:	SSH brute force attack blocker
Name:		%{name}
Version:	%{version}
Release:	%{release}
URL:		http://www.csc.liv.ac.uk/~greg/sshdfilter/
Source0:	http://www.csc.liv.ac.uk/~greg/sshdfilter-%{version}.tar.bz2
Group:		Monitoring
License:	GPL
Group:		Monitoring
Requires(post):	iptables
Requires(postun): iptables
BuildArch:	noarch
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%description
sshdfilter blocks the frequent brute force attacks on ssh daemons, it
does this by directly reading the sshd logging output and generating
iptables rules, the process can be quick enough to block an attack
before they get a chance to enter any password at all.

sshdfilter starts sshd itself, having started sshd with the -e and -D
options. This means it can see events as they happen. sshdfilter then
looks for lines of the form:

Did not receive identification string from x.x.x.x
Illegal user x from x.x.x.x
Failed password for illegal user x from x.x.x.x port x ssh2
Failed password for x from x.x.x.x port x ssh2

The former three instantly trigger sshdfilter into creating iptables
rules which block all ssh access from that IP. The latter failure is
given a few chances before it too is blocked. These are in fact example
rules, the exact wording varies between Linux distributions, so
sshdfilter exists as a base program and groups of patterns for each
distribution.

All new rules are inserted into a custom chain, and to prevent the chain
from becoming overloaded with old rules, rules over a week old are
deleted.

%package logwatch
Summary:	Logwatch scripts for sshdfilter
Group:		Monitoring
Requires:	%{name} = %{version}
Requires(post): logwatch
Requires(postun): logwatch

%description logwatch
Logwatch scripts for sshdfilter.

%prep
%setup -q

%build

%install
%{__rm} -rf %{buildroot}

%{__mkdir_p} %{buildroot}%{_sbindir}
%{__install} -m 755 sshdfilter.rhFC30 %{buildroot}%{_sbindir}/sshdfilter

%{__mkdir_p} %{buildroot}%{_sysconfdir}
%{__install} -m 644 etc/sshdfilterrc %{buildroot}%{_sysconfdir}/sshdfilterrc

%{__mkdir_p} %{buildroot}%{_sysconfdir}/log.d/{conf,scripts}/services
%{__install} -m 644 etc/log.d/conf/services/sshdfilt.conf %{buildroot}%{_sysconfdir}/log.d/conf/services/sshdfilt.conf
%{__install} -m 644 etc/log.d/scripts/services/sshdfilt %{buildroot}%{_sysconfdir}/log.d/scripts/services/sshdfilt

%{__mkdir_p} %{buildroot}%{_sysconfdir}/sysconfig
%{__cat} > %{buildroot}%{_sysconfdir}/sysconfig/sshdfilter << EOF
USE_SSHDFILTER_DEFAULT="no"
EOF

%clean
%{__rm} -rf %{buildroot}

%post
if [ -f %{_sysconfdir}/sysconfig/iptables ]; then
    %{__perl} -pi -e 's/.*SSHD.*\n//g' %{_sysconfdir}/sysconfig/iptables
    %{__perl} -pi -e 's/COMMIT\n//g' %{_sysconfdir}/sysconfig/iptables
    %{__cat} >> %{_sysconfdir}/sysconfig/iptables << EOF
:SSHD - [0:0]
-A INPUT -p tcp -m tcp --dport 22 -j SSHD
COMMIT
EOF
else
    %{__cat} > %{_sysconfdir}/sysconfig/iptables << EOF
*filter
:INPUT ACCEPT [835:105991]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [368:40879]
:SSHD - [0:0]
-A INPUT -p tcp -m tcp --dport 22 -j SSHD
COMMIT
EOF
fi
/sbin/service iptables condrestart

%postun
if [ -f %{_sysconfdir}/sysconfig/iptables ]; then
    %{__perl} -pi -e 's/.*SSHD.*\n//g' %{_sysconfdir}/sysconfig/iptables
fi
/sbin/service iptables condrestart

%post logwatch
%{__perl} -pi -e 's/ sshdfilt//g'%{_sysconfdir}/log.d/conf/services/secure.conf
%{__perl} -pi -e 's/ sshd/ sshd sshdfilt/g' %{_sysconfdir}/log.d/conf/services/secure.conf

%postun logwatch
%{__perl} -pi -e 's/ sshdfilt//g' %{_sysconfdir}/log.d/conf/services/secure.conf

%files
%defattr(-,root,root)
%doc INSTALL
%{_sbindir}/sshdfilter
%config(noreplace) %{_sysconfdir}/sshdfilterrc
%config(noreplace) %{_sysconfdir}/sysconfig/sshdfilter

%files logwatch
%defattr(-,root,root)
%config(noreplace) %{_sysconfdir}/log.d/conf/services/sshdfilt.conf
%attr(755,root,root) %{_sysconfdir}/log.d/scripts/services/sshdfilt


