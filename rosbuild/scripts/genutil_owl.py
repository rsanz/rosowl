# Software License Agreement (BSD License)
#
# Copyright (c) 2008, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

## Common generation tools for Python ROS message and service generators

from __future__ import print_function

import os
import errno  # for smart handling of exceptions for os.makedirs()
import sys
import traceback

import rospkg
import genmsg
import genowl
import genowl.generator
                
def usage(progname):
    print("%(progname)s file(s)"%vars())

def get_package_and_file(argv):
    if not argv[1:]:
        usage(argv[0])

    files = [a for a in argv[1:] if not a.startswith('--')]
    # rospy.cmake only passes in a single file arg, assert this case
    assert len(files) == 1, files

    msg_file = files[0]
    package = rospkg.get_package_name(msg_file)
    return package, msg_file

def get_outdir(package, path, subdir):
    "compute the directory that the .owl files are output to"
    outdir = os.path.join(path, 'src', package, subdir)
    if not os.path.exists(outdir):
        try:
            os.makedirs(outdir)
        except Exception as e:
            # It's not a problem if the directory already exists,
            # because this can happen during a parallel build
            if e.errno != errno.EEXIST:
                raise e
    elif not os.path.isdir(outdir): 
        raise IOError("Cannot write to %s: file in the way"%(outdir))
    return outdir

def generate_messages(rospack, package, msg_file, subdir):
    if subdir == 'msg':
        gen = genowl.generator.MsgGenerator()
    else:
        gen = genowl.generator.SrvGenerator()

    path = rospack.get_path(package)
    search_path = {
        package: [os.path.join(path, 'msg')]
        }
    # std_msgs is implicit depend due to Header
    search_path['std_msgs'] = [os.path.join(rospack.get_path('std_msgs'), 'msg')]
    for d in rospack.get_depends(package):
        search_path[d] = [os.path.join(rospack.get_path(d), 'msg')]

    include_args = []
    for d, ipaths in search_path.items():
        for ipath in ipaths:
            include_args.append('-I%s:%s'%(d, ipath))
    outdir = get_outdir(package, path, subdir)
    retcode = gen.generate_messages(package, [msg_file], outdir, search_path)
    return retcode
    
def genmain(argv, subdir):
    rospack = rospkg.RosPack()
    try:
        package, msg_file = get_package_and_file(argv)
        retcode = generate_messages(rospack, package, msg_file, subdir)

    except genmsg.InvalidMsgSpec as e:
        sys.stderr.write("ERROR: %s\n"%(str(e)))
        retcode = 1
    except genmsg.MsgGenerationException as e:
        sys.stderr.write("ERROR: %s\n"%(str(e)))
        retcode = 2
    except Exception as e:
        traceback.print_exc()
        sys.stderr.write("ERROR: %s\n"%(str(e)))
        retcode = 3
    sys.exit(retcode or 0)
