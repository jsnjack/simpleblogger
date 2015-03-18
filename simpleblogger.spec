%define name simpleblogger
%define version 2.0
%define unmangled_version 2.0
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
Requires: python-gdata >= 2.0.18
Requires: python-pygments >= 1.6


%description
blogger.com client written in Python and GTK+ 3

%prep
%setup -n %{name}-%{unmangled_version}

%build
python setup.py build

%install
python setup.py install -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
desktop-file-install %{buildroot}/usr/lib/python2.7/site-packages/simpleblogger/application/%{name}.desktop

%post
xdg-icon-resource install --novendor --size 128 /usr/lib/python2.7/site-packages/simpleblogger/application/%{name}.png

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
/usr/share/applications/simpleblogger.desktop
