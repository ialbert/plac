##########################     LICENCE     ###############################
##
##   Copyright (c) 2010, Michele Simionato
##   All rights reserved.
##
##   Redistributions of source code must retain the above copyright 
##   notice, this list of conditions and the following disclaimer.
##   Redistributions in bytecode form must reproduce the above copyright
##   notice, this list of conditions and the following disclaimer in
##   the documentation and/or other materials provided with the
##   distribution. 

##   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
##   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
##   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
##   A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
##   HOLDERS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
##   INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
##   BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
##   OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
##   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
##   TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
##   USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
##   DAMAGE.

"""
plac, the easiest Command Line Arguments Parser in the world.
See doc/plac.pdf for the documentation.
"""

__version__ = '0.5.0'

import imp, os, sys
from plac_core import *
if sys.version >= '2.5':
    from plac_ext import Interpreter, cmd_interface

try:
    PLACDIRS = os.environ.get('PLACPATH', '.').split(':')
except:
    raise ValueError('Ill-formed PLACPATH: got %PLACPATHs' % os.environ)

def import_main(path):
    "An utility to import the main function of a plac tool"
    if not os.path.isabs(path): # relative path, look at PLACDIRS
        for placdir in PLACDIRS:
            fullpath = os.path.join(placdir, path)
            if os.path.exists(fullpath):
                break
        else: # no break
            raise ImportError('Cannot find %s', path)
    else:
        fullpath = path
    name, ext = os.path.splitext(os.path.basename(fullpath))
    return imp.load_module(name, open(fullpath), fullpath, (ext, 'U', 1)).main
