%define name simpleblogger
%define version 2.4.1
%define unmangled_version 2.4.1
%define release 1

Summary: blogger.com client written in Python and GTK+ 3
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{unmangled_version}.tar.gz
License: MIT
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Yauhen Shulitski <jsnjack@gmail.com>
Url: https://github.com/e-shulitsky/simpleblogger

BuildRequires: python2-devel
BuildRequires: desktop-file-utils
BuildRequires: xdg-utils

Requires: gobject-introspection >= 1.42.0
Requires: pygobject3 >= 3.14.0
Requires: python-pip >= 6.0
Requires: python-pygments >= 1.6
Requires: python-keyring >= 8.0
Requires: python-gdata >= 2.0.18
Requires: webkitgtk4


%description
blogger.com client written in Python and GTK+ 3

%prep
%setup -n %{name}-%{unmangled_version}

%build
python setup.py build

%install
rm -rf ${RPM_BUILD_ROOT}
mkdir -p ${RPM_BUILD_ROOT}/usr/bin
python setup.py install -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
install -m 755 %{buildroot}/usr/lib/python2.7/site-packages/simpleblogger/application/%{name} ${RPM_BUILD_ROOT}%{_bindir}
desktop-file-install %{buildroot}/usr/lib/python2.7/site-packages/simpleblogger/application/%{name}.desktop

%post
xdg-icon-resource install --novendor --size 128 /usr/lib/python2.7/site-packages/simpleblogger/application/%{name}.png
pip install google-api-python-client>=1.4.0
pip install keyrings.alt

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
/usr/share/applications/simpleblogger.desktop
%attr(755,root,root) %{_bindir}/simpleblogger

%changelog
* Sun Nov 27 2016 Yauhen Shulitski <jsnjack@gmail.com> 2.4.1-1
- Update keyrings package
* Fri Oct 14 2016 Yauhen Shulitski <jsnjack@gmail.com> 2.4.0-1
- Add preview button to the headerbar
* Fri Jun 24 2016 Yauhen Shulitski <jsnjack@gmail.com> 2.3.1-1
- Style headerbar entry for gnome 3.20
* Sun Mar 6 2016 Yauhen Shulitski <jsnjack@gmail.com> 2.3-1
- Make insert code dialog scrollable
- Make preview dialog a window
* Mon Nov 9 2015 Yauhen Shulitski <jsnjack@gmail.com> 2.2-1
- Store credentials with file backend
* Tue Oct 6 2015 Yauhen Shulitski <jsnjack@gmail.com> 2.1.2-1
- Refresh token on credentials load
* Tue Oct 6 2015 Yauhen Shulitski <jsnjack@gmail.com> 2.1.1-1
- Refresh access token when uploading images to picasa
* Thu Sep 10 2015 Yauhen Shulitski <jsnjack@gmail.com> 2.1-1
- Update application to use Oauth2 for google services
* Thu May 21 2015 Yauhen Shulitski <jsnjack@gmail.com> 2.0.1-1
- Save latest used language for code insert dialog
