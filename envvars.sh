# Source this to set the necessary env vars.

antelope=/opt/antelope/5.3pre

. $antelope/setup.sh

# Config PF location
export PFPATH=$PFPATH:`pwd`/etc
export ANTELOPE_PYTHON_GILRELEASE=1

. ../pydlmon-ve-new/bin/activate

