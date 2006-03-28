/*
 * module.hpp
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

#ifndef MODULE_HPP
#define MODULE_HPP

#define DISABLE_TEMPLATES
#include "elf.hpp"
#include "module_devicetable.hpp"

#include <list>
#include <map>
#include <ostream>

namespace linuxkernel
{
  class modulelist;
  class symbolname;
  class symbol_exported;
  class symbol_undefined;

  class module
  {
    public:
      typedef std::map<std::string, symbol_exported> _symbols_exported;

      module (const std::string &name) throw ();

      bool get_is_vmlinux () const throw () { return is_vmlinux; }
      const std::string &get_name () const throw () { return name; }
      const std::string &get_name_short () const throw () { return name_short; }
      const _symbols_exported &get_symbols_exported () const throw () { return symbols_exported; }

    protected:
      module (const std::string &filename, bool) throw ();

      std::string name, name_short;
      bool is_vmlinux;
      _symbols_exported symbols_exported;

      friend class modulelist;
  };

  class module_real : public module
  {
    public:
      typedef std::map<std::string, symbol_undefined> _symbols_undefined;

      module_real (const std::string &filename, Elf::file *file) throw (std::runtime_error);

      const Elf::symbol *_get_symbol (const std::string &name) const throw ();

      void write (const modulelist &, bool modversions);

      static module_real *open (const std::string &filename) throw (std::bad_alloc, std::runtime_error);

      const static std::string symbol_name_cleanup;
      const static std::string symbol_name_init;
      const static std::string symbol_prefix_crc;
      const static std::string symbol_prefix_ksymtab;

    protected:
      template<typename Elf_class>
        static module_real *open_class (const std::string &filename, Elf::file *) throw (std::bad_alloc, std::runtime_error);

      void read_modinfo (Elf::section *) throw (std::runtime_error);
      void read_symtab (Elf::section_type<Elf::section_type_SYMTAB> *) throw (std::runtime_error);

      void write_depends (std::ostream &, const modulelist &);
      void write_header (std::ostream &);
      void write_moddevtable (std::ostream &);
      void write_versions (std::ostream &, const modulelist &);

      std::map<std::string, std::string> modinfo;
      _symbols_undefined symbols_undefined;
      bool has_init;
      bool has_cleanup;
      Elf::section_type<Elf::section_type_SYMTAB> *symtab;
      std::list<module_devicetable::table_base *> devicetables;

      Elf::file *file;
  };

  template <typename Elf_class, typename Elf_data>
    class module_data : public module_real
    {
      public:
        module_data (const std::string &filename, Elf::file *file) throw (std::runtime_error);
    };

  class modulelist
  {
    public:
      typedef std::map<std::string, module_real *> _modules_real;
      typedef std::pair<std::string, module_real *> _modules_real_pair;
      typedef std::map<std::string, module *> _modules_shadow;
      typedef std::pair<std::string, module *> _modules_shadow_pair;
      typedef std::map<std::string, std::string> _symbols;

      modulelist () throw ();
      ~modulelist () throw ();

      void dump_read (const std::string &filename) throw (std::runtime_error);
      void dump_write (const std::string &filename) const throw (std::runtime_error);

      const _modules_real &get_modules_real () const throw () { return modules_real; }
      const _modules_shadow &get_modules_shadow () const throw () { return modules_shadow; }
      const module *get_module (const std::string &name) const throw (std::out_of_range);
      const module *get_module_for_symbol (const symbolname &name) const throw (std::out_of_range);
      const std::string &get_module_name_short_for_symbol (const symbolname &name) const throw (std::out_of_range);
      const symbol_exported &get_symbol (const symbolname &name) const throw (std::out_of_range);
      const _symbols &get_symbols_exported () const throw () { return symbols_exported; }

      void insert (module_real *) throw (std::runtime_error);
      void insert (const std::string &filename) throw (std::runtime_error);

      void write (bool modversions);

      bool report_symbols_missing;

    protected:
      _modules_real modules_real;
      _modules_shadow modules_shadow;
      _symbols symbols_exported;
  };

  class symbolname : public std::string
  {
    public:
      symbolname () throw () {}
      symbolname (const std::string &name) throw ()
      : std::string (name)
      {
        if (size () && at (0) == '.')
          erase (0, 1);
      }
      symbolname (const char *name) throw ()
      : std::string (name)
      {
        if (size () && at (0) == '.')
          erase (0, 1);
      }
  };

  class symbol
  {
    public:
      symbol () throw () {}
      symbol (const symbolname &name) throw ();

      const symbolname &get_name () const throw () { return name; }

    protected:
      symbolname name;
  };

  class symbol_exported : public symbol
  {
    public:
      symbol_exported () throw () {}
      symbol_exported (const symbolname &name) throw ();
      symbol_exported (const symbolname &name, uint32_t) throw ();

      uint32_t get_crc () const throw () { return crc; }
      bool get_crc_valid () const throw () { return crc_valid; }
      void set_crc (uint32_t) throw ();

    protected:
      uint32_t crc;
      bool crc_valid;
  };

  class symbol_undefined : public symbol
  {
    public:
      symbol_undefined () throw () {}
      symbol_undefined (const symbolname &name, bool weak) throw ();

    protected:
      bool weak;
  };
}

#include "module_devicetable.tpp"

#undef DISABLE_TEMPLATES
#endif
