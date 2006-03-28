/*
 * module_devicetable.cpp
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

#include "module.hpp"
#include "module_devicetable.hpp"

namespace linuxkernel
{
  namespace module_devicetable
  {
    namespace internal
    {
      const std::string def<device_ccw>::symbol = "__mod_ccw_device_table";
      const std::string def<device_i2c>::symbol = "__mod_i2c_device_table";
      const std::string def<device_ieee1394>::symbol = "__mod_ieee1394_device_table";
      const std::string def<device_input>::symbol = "__mod_input_device_table";
      const std::string def<device_of>::symbol = "__mod_of_device_table";
      const std::string def<device_pci>::symbol = "__mod_pci_device_table";
      const std::string def<device_pcmcia>::symbol = "__mod_pcmcia_device_table";
      const std::string def<device_pnp>::symbol = "__mod_pnp_device_table";
      const std::string def<device_pnp_card>::symbol = "__mod_pnp_card_device_table";
      const std::string def<device_serio>::symbol = "__mod_serio_device_table";
      const std::string def<device_usb>::symbol = "__mod_usb_device_table";
      const std::string def<device_vio>::symbol = "__mod_vio_device_table";
    }

    void table_base::write (std::ostream &out) const throw (std::runtime_error)
    { 
      for (std::list<table_entry *>::const_iterator it = entries.begin (); it != entries.end (); ++it)
      { 
        out << "MODULE_ALIAS(\"";
        (*it)->write (out);
        out << "\");\n";
      }
    }
  }
}
