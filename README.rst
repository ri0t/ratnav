RatNav
======

This application is meant to help you drive your car more efficient.

Run it on an embedded Debian system with a camera and speaker attached.

Mount the camera on top of your dashboard so it sees the traffic in front of
you.

Hopefully, the system will accoustically guide you through traffic at a better
efficiency ;)

Source & Issues
===============

Ratnav currently lives here:
    https://github.com/ri0t/ratnav
We use github's nice issue tracker to dissect and kill bugs:
    https://github.com/ri0t/ratnav/issues

Installation
============

Ideally, you're running Debian. You'll need python-opencv and some other stuff
installed:

    sudo apt-get install python-opencv python-numpy

Then you can install ratnav itself:

    sudo python setup.py install

This should be everything necessary to run RatNav.

Copyright, License
==================

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <http://www.gnu.org/licenses/>.

Contributors
============

This utility was conceived by David Riding and Heiko Weinen at Betahaus in 2014
and is in part based on Robin David's work, which you can find at
https://github.com/RobinDavid/Motion-detection-OpenCV.git

* David Riding
* Heiko 'riot' Weinen <riot@hackerfleet.org>
* Robin David
* KDE4 Granatier application for the 'yippie' sound
