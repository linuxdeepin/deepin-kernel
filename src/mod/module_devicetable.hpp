/*
 * module_devicetable.hpp
 *
 * Copyright (C) 2005, 2006 Bastian Blank <waldi@debian.org>
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

#ifndef MODULE_DEVICETABLE_HPP
#define MODULE_DEVICETABLE_HPP

#include "elf.hpp"

#include <list>
#include <ostream>
#include <stdexcept>

namespace linuxkernel
{
  class module_real;

  namespace module_devicetable
  {
    class device_ccw { };
    class device_i2c { };
    class device_ieee1394 { };
    class device_input { };
    class device_of { };
    class device_pci { };
    class device_pcmcia { };
    class device_pnp { };
    class device_pnp_card { };
    class device_serio { };
    class device_usb { };
    class device_vio { };

    class version_2_6_16 { };

    namespace internal
    {
      template<typename device>
        struct def {};
      template<> struct def<device_ccw> { static const std::string symbol; };
      template<> struct def<device_i2c> { static const std::string symbol; };
      template<> struct def<device_ieee1394> { static const std::string symbol; };
      template<> struct def<device_input> { static const std::string symbol; };
      template<> struct def<device_of> { static const std::string symbol; };
      template<> struct def<device_pci> { static const std::string symbol; };
      template<> struct def<device_pcmcia> { static const std::string symbol; };
      template<> struct def<device_pnp> { static const std::string symbol; };
      template<> struct def<device_pnp_card> { static const std::string symbol; };
      template<> struct def<device_serio> { static const std::string symbol; };
      template<> struct def<device_usb> { static const std::string symbol; };
      template<> struct def<device_vio> { static const std::string symbol; };
    }

    class table_entry
    {
      public:
        virtual ~table_entry () {};
        virtual void write (std::ostream &) const throw (std::runtime_error) = 0;
    };

    template<typename device, typename version>
      class table_entry_version : public table_entry
      {
      };

    template<typename device, typename version, typename Elf_class, typename Elf_data>
      class table_entry_data : public table_entry_version<device, version>
      {
      };

    class table_base
    {
      public:
        virtual ~table_base () throw () {};

        void write (std::ostream &out) const throw (std::runtime_error);


      protected:
        table_base () throw () {};

        std::list<table_entry *> entries;
    };

    template<typename Elf_class, typename Elf_data>
      void table_create (std::list<table_base *> &, const module_real *m, const Elf::file *f) throw (std::runtime_error);

    template<typename device, typename Elf_class, typename Elf_data>
      class table : public table_base
      {
        public:
          static table_base *create (const module_real *m, const Elf::file *f) throw (std::runtime_error);

        protected:
          table () {};
      };

    template<typename device, typename version, typename Elf_class, typename Elf_data>
      class table_data : public table<device, Elf_class, Elf_data>
      { 
        public:
          table_data (const void *, size_t) throw (std::runtime_error);
      };
  }
}

#ifndef DISABLE_TEMPLATES
#include "module_devicetable.tpp"
#endif

#endif
