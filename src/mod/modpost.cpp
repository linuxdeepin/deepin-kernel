/*
 * modpost.cpp
 *
 * Copyright (C) 2005 Bastian Blank <waldi@debian.org>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 */

#include "elf.hpp"
#include "module.hpp"

#include <iostream>

#include <getopt.h>

using namespace linuxkernel;

modulelist modules;

int main (int argc, char *const argv[])
{
  int ret = EXIT_SUCCESS;
  int opt;
  const char *dump_read = 0, *dump_write = 0;
  bool all_versions = false, modversions = false;;

  while ((opt = getopt (argc, argv, "ai:mo:")) != -1)
  {
    switch(opt) {
      case 'a':
        all_versions = true;
        std::clog << "*** Warning: CONFIG_MODULE_SRCVERSION_ALL is not supported!" << std::endl;
        return EXIT_FAILURE;
        break;
      case 'i':
        dump_read = optarg;
        break;
      case 'm':
        modversions = true;
        break;
      case 'o':
        dump_write = optarg;
        break;
      default:
        exit(1);
    }
  }

  if (dump_read)
    modules.dump_read (dump_read);

  for (int i = optind; i < argc; i++)
  {
    std::string filename (argv[i]);
    try
    {
      modules.insert (filename);
    }
    catch (std::runtime_error &e)
    {
      std::clog << "*** Warning: \"" << filename << "\" failed to load: " << e.what () << std::endl;
      ret = EXIT_FAILURE;
      continue;
    }
  }
  modules.write (modversions);

  if (dump_write)
    modules.dump_write (dump_write);

  return ret;
}
