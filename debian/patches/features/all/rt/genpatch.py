#!/usr/bin/python

import os, os.path, re, shutil, subprocess, sys

def main(source_dir, version=None):
    patch_dir = 'debian/patches'
    rt_patch_dir = 'features/all/rt'
    series_name = 'series-rt'
    old_series = set()
    new_series = set()

    with open(os.path.join(patch_dir, series_name), 'r') as series_fh:
        for line in series_fh:
            name = line.strip()
            if name != '' and name[0] != '#':
                old_series.add(name)

    with open(os.path.join(patch_dir, series_name), 'w') as series_fh:
        # Add directory prefix to all filenames
        def add_patch(name):
            name = os.path.join(rt_patch_dir, name)
            series_fh.write(name)
            series_fh.write('\n')
            new_series.add(name)

        if version:
            # Export rebased branch from stable-rt git as patch series
            up_ver = re.sub(r'-rt\d+$', '', version)
            args = ['git', 'format-patch', 'v%s..v%s-rebase' % (up_ver, version)]
            env = os.environ.copy()
            env['GIT_DIR'] = os.path.join(source_dir, '.git')
            child = subprocess.Popen(args,
                                     cwd=os.path.join(patch_dir, rt_patch_dir),
                                     env=env, stdout=subprocess.PIPE)
            with child.stdout as pipe:
                for line in pipe:
                    name = line.strip('\n')
                    add_patch(name)
        else:
            # Copy patch series
            with open(os.path.join(source_dir, 'series'), 'r') as \
                    source_series_fh:
                for line in source_series_fh:
                    name = line.strip()
                    if name != '' and name[0] != '#':
                        shutil.copyfile(os.path.join(source_dir, name),
                                        os.path.join(patch_dir, rt_patch_dir,
                                                     name))
                        add_patch(name)
                    else:
                        # Leave comments and empty lines unchanged
                        series_fh.write(line)

    for name in new_series:
        if name in old_series:
            old_series.remove(name)
        else:
            print 'Added patch', os.path.join(patch_dir, name)

    for name in old_series:
        print 'Obsoleted patch', os.path.join(patch_dir, name)

if __name__ == '__main__':
    if len(sys.argv) not in [2, 3]:
        print >>sys.stderr, '''\
Usage: %s REPO RT-VERSION
       %s QUILT-DIR''' % (sys.argv[0], sys.argv[0])
        sys.exit(2)
    main(*sys.argv[1:])
