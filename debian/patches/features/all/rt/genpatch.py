#!/usr/bin/python

import os, os.path, re, subprocess, sys

def main(repo, version):
    up_ver = re.sub(r'-rt\d+$', '', version)
    patch_dir = 'debian/patches/features/all/rt'
    old_series = set()

    with open(os.path.join(patch_dir, 'series'), 'r') as series_fh:
        for line in series_fh:
            name = line.strip()
            if name != '' and name[0] != '#':
                old_series.add(name)

    with open(os.path.join(patch_dir, 'series'), 'w') as series_fh:
        args = ['git', 'format-patch', 'v%s..v%s-rebase' % (up_ver, version)]
        env = os.environ.copy()
        env['GIT_DIR'] = os.path.join(repo, '.git')
        child = subprocess.Popen(args, cwd=patch_dir, env=env,
                                 stdout=subprocess.PIPE)
        with child.stdout as pipe:
            for line in pipe:
                series_fh.write(line)
                name = line.strip('\n')
                if name in old_series:
                    old_series.remove(name)
                else:
                    print 'Added patch', os.path.join(patch_dir, name)

    for name in old_series:
        print 'Obsoleted patch', os.path.join(patch_dir, name)

    subprocess.check_call([os.path.join(patch_dir, 'convert-series')])

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print >>sys.stderr, "Usage: %s REPO RT-VERSION" % sys.argv[0]
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
