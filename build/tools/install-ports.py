#!/usr/bin/env python2.7
#+
# Copyright 2015 iXsystems, Inc.
# All rights reserved
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted providing that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
#####################################################################


import os
import sys
import glob
from dsl import load_profile_config
from utils import sh, setup_env, objdir, info, debug, error, setfile, e, on_abort, chroot, get_port_names, readfile


config = load_profile_config()
logfile = objdir('logs/pkg-install')


def mount_packages():
    on_abort(umount_packages)
    jailname = readfile(e('${OBJDIR}/jailname'))
    sh('mkdir -p ${WORLD_DESTDIR}/usr/ports/packages')
    sh('mount -t nullfs ${OBJDIR}/ports/packages/${jailname}-p ${WORLD_DESTDIR}/usr/ports/packages')


def umount_packages():
    sh('umount ${WORLD_DESTDIR}/usr/ports/packages')
    on_abort(None)


def create_pkgng_configuration():
    sh('mkdir -p ${WORLD_DESTDIR}/usr/local/etc/pkg/repos')
    for i in glob.glob(e('${BUILD_CONFIG}/templates/pkg-repos/*')):
        fname = os.path.basename(i)
        sh(e('cp ${i} ${WORLD_DESTDIR}/usr/local/etc/pkg/repos/${fname}'))


def install_ports():
    pkgs = ' '.join(get_port_names(config.ports))
    chroot('${WORLD_DESTDIR}', 'env ASSUME_ALWAYS_YES=yes pkg install -r local -f ${pkgs}', log=logfile)

    if not os.path.exists(e('${WORLD_DESTDIR}/etc/freenas.conf')):
        error('Packages installation failed, see {0}', logfile)


if __name__ == '__main__':
    if e('${SKIP_PORTS_INSTALL}'):
        info('Skipping ports install as instructed by setting SKIP_PORTS_INSTALL')
        sys.exit(0)

    info('Installing ports')
    info('Log file: {0}', logfile)
    mount_packages()
    create_pkgng_configuration()
    install_ports()
    umount_packages()