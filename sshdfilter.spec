%bcond_with     logwatch

Name:           sshdfilter
Version:        1.5.4
Release:        %mkrel 2
Epoch:          0
Summary:        SSH brute force attack blocker
License:        GPL
Group:          Monitoring
URL:            http://www.csc.liv.ac.uk/~greg/sshdfilter/
Source0:        http://www.csc.liv.ac.uk/~greg/sshdfilter-%{version}.tar.gz
Requires(post): iptables
Requires(postun): iptables
Requires(post): openssh-server
Requires(postun): openssh-server
BuildArch:        noarch
BuildRoot:        %{_tmppath}/%{name}-%{version}-%{epoch}:%{release}-root

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

%if %with logwatch
%package logwatch
Summary:        Logwatch scripts for sshdfilter
Group:          Monitoring
Requires:       %{name} = %{epoch}:%{version}-%{release}
Requires(post): logwatch
Requires(postun): logwatch

%description logwatch
Logwatch scripts for sshdfilter.
%endif

%prep
%setup -q

%build

%install
%{__rm} -rf %{buildroot}

%{__mkdir_p} %{buildroot}%{_sysconfdir}
%{__cat} etc/sshdfilterrc patterns/rhFC30.partconf > %{buildroot}%{_sysconfdir}/sshdfilterrc

%{__mkdir_p} %{buildroot}%{_sbindir}
%{__cp} -a source/sshdfilter.pl %{buildroot}%{_sbindir}/sshdfilter

(cd man; sh ./pod2man.sh)
%{__mkdir_p} %{buildroot}%{_mandir}/man1
%{__cp} -a man/sshdfilter.1 %{buildroot}%{_mandir}/man1/sshdfilter.1
%{__mkdir_p} %{buildroot}%{_mandir}/man5
%{__cp} -a man/sshdfilterrc.5 %{buildroot}%{_mandir}/man5/sshdfilterrc.5

%if %with logwatch
%{__mkdir_p} %{buildroot}%{_sysconfdir}/log.d/{conf,scripts}/services
%{__install} -m 644 etc/log.d/conf/services/sshdfilt.conf %{buildroot}%{_sysconfdir}/log.d/conf/services/sshdfilt.conf
%{__install} -m 644 etc/log.d/scripts/services/sshdfilt %{buildroot}%{_sysconfdir}/log.d/scripts/services/sshdfilt
%endif

%{__mkdir_p} %{buildroot}%{_sysconfdir}/sysconfig
%{__cat} > %{buildroot}%{_sysconfdir}/sysconfig/sshdfilter << EOF
USE_SSHDFILTER_DEFAULT="no"
EOF

%clean
%{__rm} -rf %{buildroot}

%post
if [ -r %{_sysconfdir}/sysconfig/iptables ]; then
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
/sbin/service sshd condrestart

%postun
if [ -r %{_sysconfdir}/sysconfig/iptables ]; then
    %{__perl} -pi -e 's/.*SSHD.*\n//g' %{_sysconfdir}/sysconfig/iptables
fi
/sbin/service iptables condrestart
/sbin/service sshd condrestart

%if %with logwatch
%post logwatch
%{__perl} -pi -e 's/ sshdfilt//g'%{_sysconfdir}/log.d/conf/services/secure.conf
%{__perl} -pi -e 's/ sshd/ sshd sshdfilt/g' %{_sysconfdir}/log.d/conf/services/secure.conf

%postun logwatch
%{__perl} -pi -e 's/ sshdfilt//g' %{_sysconfdir}/log.d/conf/services/secure.conf
%endif

%files
%defattr(0644,root,root,0755)
%doc INSTALL todo
%attr(0755,root,root) %{_sbindir}/sshdfilter
%{_mandir}/man1/sshdfilter.1*
%{_mandir}/man5/sshdfilterrc.5*
%config(noreplace) %{_sysconfdir}/sshdfilterrc
%config(noreplace) %{_sysconfdir}/sysconfig/sshdfilter

%if %with logwatch
%files logwatch
%defattr(0644,root,root,0755)
%config(noreplace) %{_sysconfdir}/log.d/conf/services/sshdfilt.conf
%attr(0755,root,root) %{_sysconfdir}/log.d/scripts/services/sshdfilt
%endif

