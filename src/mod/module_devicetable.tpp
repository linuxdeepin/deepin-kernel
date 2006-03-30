/*
 * module_devicetable.tpp
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

#ifndef MODULE_DEVICETABLE_TPP
#define MODULE_DEVICETABLE_TPP

#include "module.hpp"

namespace linuxkernel
{
  namespace module_devicetable
  {
    template<typename Elf_class, typename Elf_data>
      void table_create (std::list<table_base *> &list, const module_real *m, const Elf::file *file) throw (std::runtime_error)
      {
        list.push_back (table<module_devicetable::device_ccw, Elf_class, Elf_data>::create (m, file));
        list.push_back (table<module_devicetable::device_i2c, Elf_class, Elf_data>::create (m, file));
        list.push_back (table<module_devicetable::device_ieee1394, Elf_class, Elf_data>::create (m, file));
        list.push_back (table<module_devicetable::device_input, Elf_class, Elf_data>::create (m, file));
        list.push_back (table<module_devicetable::device_of, Elf_class, Elf_data>::create (m, file));
        list.push_back (table<module_devicetable::device_pci, Elf_class, Elf_data>::create (m, file));
        list.push_back (table<module_devicetable::device_pcmcia, Elf_class, Elf_data>::create (m, file));
        list.push_back (table<module_devicetable::device_pnp, Elf_class, Elf_data>::create (m, file));
        list.push_back (table<module_devicetable::device_pnp_card, Elf_class, Elf_data>::create (m, file));
        list.push_back (table<module_devicetable::device_serio, Elf_class, Elf_data>::create (m, file));
        list.push_back (table<module_devicetable::device_usb, Elf_class, Elf_data>::create (m, file));
        list.push_back (table<module_devicetable::device_vio, Elf_class, Elf_data>::create (m, file));
      }

    template<typename device, typename Elf_class, typename Elf_data>
      table_base *table<device, Elf_class, Elf_data>::create (const module_real *m, const Elf::file *f) throw (std::runtime_error)
      {
        const Elf::symbol *sym = m->_get_symbol (internal::def<device>::symbol);
        if (!sym)
          return 0;
        const Elf::section *sec = f->get_section (sym->get_shndx ());
        const char *mem = static_cast <const char *> (sec->_mem ());
        return new table_data<device, version_2_6_16, Elf_class, Elf_data> (mem + sym->get_value (), sym->get_size ());
      }
  }
}

#endif
