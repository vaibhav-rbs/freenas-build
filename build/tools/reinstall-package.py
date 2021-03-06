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
from utils import glob, sh, setup_env


def main():
    pkg_paths = []
    pkg_names = []
    for i in glob('${OBJDIR}/ports/packages/*/All/${package}*.txz'):
        pkg_paths.append(i)
        pkg_names.append(os.path.basename(i))

    pkg_dest_paths = ' '.join([os.path.join('/tmp', i) for i in pkg_names])
    pkg_paths = ' '.join(pkg_paths)
    pkg_names = ' '.join(pkg_names)
    sh('scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ${pkg_paths} ${host}:/tmp/')
    sh('ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -t ${host} pkg add -f ${pkg_dest_paths}')


if __name__ == '__main__':
    main()