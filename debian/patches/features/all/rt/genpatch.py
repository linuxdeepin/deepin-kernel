#!/usr/bin/python

import os, os.path, re, shutil, subprocess, sys

def main(source_dir, version=None):
    patch_dir = 'debian/patches/features/all/rt'
    old_series = set()
    new_series = set()

    with open(os.path.join(patch_dir, 'series'), 'r') as series_fh:
        for line in series_fh:
            name = line.strip()
            if name != '' and name[0] != '#':
                old_series.add(name)

    if version:
        # Export rebased branch from stable-rt git as patch series
        up_ver = re.sub(r'-rt\d+$', '', version)
        with open(os.path.join(patch_dir, 'series'), 'w') as series_fh:
            args = ['git', 'format-patch', 'v%s..v%s-rebase' % (up_ver, version)]
            env = os.environ.copy()
            env['GIT_DIR'] = os.path.join(source_dir, '.git')
            child = subprocess.Popen(args, cwd=patch_dir, env=env,
                                     stdout=subprocess.PIPE)
            with child.stdout as pipe:
                for line in pipe:
                    series_fh.write(line)
                    name = line.strip('\n')
                    new_series.add(name)
    else:
        # Copy patch series
        shutil.copyfile(os.path.join(source_dir, 'series'),
                        os.path.join(patch_dir, 'series'))
        with open(os.path.join(patch_dir, 'series'), 'r') as series_fh:
            for line in series_fh:
                name = line.strip()
                if name != '' and name[0] != '#':
                    shutil.copyfile(os.path.join(source_dir, name),
                                    os.path.join(patch_dir, name))
                    new_series.add(name)

    for name in new_series:
        if name in old_series:
            old_series.remove(name)
        else:
            print 'Added patch', os.path.join(patch_dir, name)

    for name in old_series:
        print 'Obsoleted patch', os.path.join(patch_dir, name)

    subprocess.check_call([os.path.join(patch_dir, 'convert-series')])

if __name__ == '__main__':
    if len(sys.argv) not in [2, 3]:
        print >>sys.stderr, '''\
Usage: %s REPO RT-VERSION
       %s QUILT-DIR''' % (sys.argv[0], sys.argv[0])
        sys.exit(2)
    main(*sys.argv[1:])
