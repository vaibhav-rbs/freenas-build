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
import string
from dsl import load_file, load_profile_config
from utils import sh, sh_str, env, e, objdir, pathjoin, setfile, setup_env, template, debug, error, on_abort, info


makejobs = 1
jailname = None
config = load_profile_config()
installer_ports = load_file('${BUILD_CONFIG}/ports-installer.pyd', os.environ)
jailconf = load_file('${BUILD_CONFIG}/jail.pyd', os.environ)

portslist = e('${POUDRIERE_ROOT}/etc/ports.conf')
portoptions = e('${POUDRIERE_ROOT}/etc/poudriere.d/options')


def calculate_make_jobs():
    global makejobs

    jobs = sh_str('sysctl -n kern.smp.cpus')
    if not jobs:
        makejobs = 2

    makejobs = int(jobs) + 1
    debug('Using {0} make jobs', makejobs)


def create_overlay():
    sh('rm -rf ${PORTS_OVERLAY}')
    sh('mkdir -p ${PORTS_OVERLAY}')
    sh('mount_unionfs -o below ${PORTS_ROOT} ${PORTS_OVERLAY}')


def create_poudriere_config():
    sh('mkdir -p ${DISTFILES_CACHE}')
    setfile('${POUDRIERE_ROOT}/etc/poudriere.conf', template('${BUILD_CONFIG}/templates/poudriere.conf', {
        'ports_repo': config['repos'].where(name='ports')['path'],
        'ports_branch': config['repos'].where(name='ports')['branch'],
    }))

    tree = e('${POUDRIERE_ROOT}/etc/poudriere.d/ports/p')
    sh('mkdir -p', tree)
    setfile(pathjoin(tree, 'mnt'), e('${PORTS_OVERLAY}'))
    setfile(pathjoin(tree, 'method'), 'git')


def create_make_conf():
    makeconf = e('${POUDRIERE_ROOT}/etc/poudriere.d/make.conf')
    setfile(makeconf, template('${BUILD_CONFIG}/templates/poudriere-make.conf'))


def create_ports_list():
    info('Creating ports list')
    sh('rm -rf', portoptions)

    f = open(portslist, 'w')
    for port in installer_ports['ports'] + config['ports']:
        name = port['name'] if isinstance(port, dict) else port
        name_und = name.replace('/', '_')
        options_path = pathjoin(portoptions, name_und)
        f.write('{0}\n'.format(name))

        sh('mkdir -p', options_path)
        if isinstance(port, dict) and 'options' in port:
            opt = open(pathjoin(options_path, 'options'), 'w')
            for o in port['options']:
                opt.write('{0}\n'.format(o))

            opt.close()

    f.close()


def obtain_jail_name():
    global jailname
    for i in string.ascii_lowercase:
        if sh('jls -q -n -j j${i}-p', log="/dev/null", nofail=True) != 0:
            jailname = e('j${i}')
            setfile(e('${OBJDIR}/jailname'), jailname)
            return

    error('No jail names available')


def prepare_jail():
    basepath = e('${POUDRIERE_ROOT}/etc/poudriere.d/jails/${jailname}')
    sh('mkdir -p ${basepath}')

    setfile(e('${basepath}/method'), 'git')
    setfile(e('${basepath}/mnt'), e('${JAIL_DESTDIR}'))
    setfile(e('${basepath}/version'), e('${FREEBSD_RELEASE_VERSION}'))
    setfile(e('${basepath}/arch'), e('${BUILD_ARCH}'))

    sh("jail -U root -c name=${jailname} path=${JAIL_DESTDIR} command=/sbin/ldconfig -m /lib /usr/lib /usr/lib/compat")


def merge_freenas_ports():
    sh('mkdir -p ${PORTS_OVERLAY}/freenas')
    sh('cp -a ${FREENAS_ROOT}/nas_ports/freenas ${PORTS_OVERLAY}/')


def prepare_env():
    for cmd in jailconf.get('copy', []):
        dest = os.path.join(e('${JAIL_DESTDIR}'), cmd['dest'][1:])
        sh('rm -rf ${dest}')
        sh('cp -a', cmd['source'], dest)

    for cmd in jailconf.get('link', []):
        flags = '-o {0}'.format(cmd['flags']) if 'flags' in cmd else ''
        dest = os.path.join(e('${JAIL_DESTDIR}'), cmd['dest'][1:])
        sh('mkdir -p', os.path.dirname(dest))
        sh('mount -t nullfs', flags, cmd['source'], dest)

    osversion=sh_str("awk '/\#define __FreeBSD_version/ { print $3 }' ${JAIL_DESTDIR}/usr/include/sys/param.h")
    login_env = e(',UNAME_r=${FREEBSD_RELEASE_VERSION% *},UNAME_v=FreeBSD ${FREEBSD_RELEASE_VERSION},OSVERSION=${osversion}')
    sh('sed -i "" -e "s/,UNAME_r.*:/:/ ; s/:\(setenv.*\):/:\\1${login_env}:/" ${JAIL_DESTDIR}/etc/login.conf')
    sh('cap_mkdb ${JAIL_DESTDIR}/etc/login.conf');

def cleanup_env():
    sh('umount -f ${PORTS_OVERLAY}')
    sh('rm -rf ${PORTS_OVERLAY}')
    for cmd in jailconf.get('link', []):
        sh('umount -f', cmd['source'])


def run():
    sh('poudriere -e ${POUDRIERE_ROOT}/etc bulk -w -J', str(makejobs), '-f', portslist, '-j ${jailname} -p p')


if __name__ == '__main__':
    if env('SKIP_PORTS'):
        info('Skipping ports build as instructed by setting SKIP_PORTS')
        sys.exit(0)

    create_overlay()
    on_abort(cleanup_env)
    obtain_jail_name()
    calculate_make_jobs()
    create_poudriere_config()
    create_make_conf()
    create_ports_list()
    prepare_jail()
    merge_freenas_ports()
    prepare_env()
    run()
    cleanup_env()
