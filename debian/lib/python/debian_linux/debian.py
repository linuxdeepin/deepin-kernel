import re, utils

def read_changelog():
    r = re.compile(r"""
^
(
(?P<header>
    (?P<header_source>
        \w[-+0-9a-z.]+
    )
    \ 
    \(
    (?P<header_version>
        [^\(\)\ \t]+
    )
    \)
    \s+
    (?P<header_distribution>
        [-0-9a-zA-Z]+
    )
    \;
)
)
""", re.VERBOSE)
    f = file("debian/changelog")
    entries = []
    act_upstream = None
    while True:
        line = f.readline()
        if not line:
            break
        line = line.strip('\n')
        match = r.match(line)
        if not match:
            continue
        if match.group('header'):
            e = {}
            e['Distribution'] = match.group('header_distribution')
            e['Source'] = match.group('header_source')
            version = parse_version(match.group('header_version'))
            e['Version'] = version
            if act_upstream is None:
                act_upstream = version['upstream']
            elif version['upstream'] != act_upstream:
                break
            entries.append(e)
    return entries

def parse_version(version):
    version_re = ur"""
^
(?P<source>
    (?P<parent>
        \d+\.\d+\.\d+\+
    )?
    (?P<upstream>
        (?P<version>
            (?P<major>\d+\.\d+)
            \.
            \d+
        )
        (?:
            -
            (?P<modifier>
                .+?
            )
        )?
    )
    -
    (?P<debian>[^-]+)
)
$
"""
    match = re.match(version_re, version, re.X)
    if match is None:
        raise ValueError
    ret = match.groupdict()
    if ret['parent'] is not None:
        ret['source_upstream'] = ret['parent'] + ret['upstream']
    else:
        ret['source_upstream'] = ret['upstream']
    return ret

