/*
 * module.cpp
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

#include <fstream>
#include <iostream>
#include <sstream>
#include <set>

#include <elf.h>

using namespace linuxkernel;

const std::string module_real::symbol_name_cleanup ("cleanup_module");
const std::string module_real::symbol_name_init ("init_module");
const std::string module_real::symbol_prefix_crc ("__crc_");
const std::string module_real::symbol_prefix_ksymtab ("__ksymtab_");

module::module (const std::string &name) throw ()
: name (name)
{
  std::string::size_type t1 = name.find_last_of ('/');
  if (t1 == std::string::npos)
    t1 = 0;
  else
    t1++;
  name_short = name.substr (t1, std::string::npos);

  if (name == "vmlinux")
    is_vmlinux = true;
}

module::module (const std::string &filename, bool) throw ()
{
  std::string::size_type t1 = filename.find_last_of ('/');
  std::string::size_type t2 = filename.find_last_of ('.');
  if (t1 == std::string::npos)
    t1 = 0;
  else
    t1++;
  name = filename.substr (0, t2);
  if (t2 != std::string::npos)
    t2 -= t1;
  name_short = filename.substr (t1, t2);

  if (name == "vmlinux")
    is_vmlinux = true;
}

module_real::module_real (const std::string &filename, Elf::file *file) throw (std::runtime_error)
: module (filename, false), has_init (false), has_cleanup (false), file (file)
{
  const std::vector <Elf::section *> &sections = file->get_sections ();
  Elf::section *modinfo = 0;
  symtab = 0;

  for (std::vector <Elf::section *>::const_iterator it = sections.begin (); it != sections.end (); ++it)
  {
    const std::string &name = (*it)->get_name_string ();
    uint32_t type = (*it)->get_type ();
    if (name == ".modinfo")
      modinfo = *it;
    if (type == Elf::section_type_SYMTAB::id)
      symtab = dynamic_cast <Elf::section_type<Elf::section_type_SYMTAB> *> (*it);
  }

  if (!is_vmlinux && !modinfo)
    throw std::runtime_error ("Not a kernel module, lacks modinfo section");
  if (!symtab)
    throw std::runtime_error ("Not a kernel module, lacks symbol table");

  if (!is_vmlinux)
  {
    read_modinfo (modinfo);
    symbols_undefined.insert (std::pair<std::string, symbol_undefined> ("struct_module", symbol_undefined ("struct_module", 0)));
  }
  read_symtab (symtab);
}

const Elf::symbol *module_real::_get_symbol (const std::string &name) const throw ()
{
  for (std::vector<Elf::symbol *>::const_iterator it = symtab->get_symbols ().begin (); it != symtab->get_symbols ().end (); ++it)
  {
    Elf::symbol *symbol = *it;
    std::string symname = symbol->get_name_string ();
    if (symname == name)
      return symbol;
  }
  return 0;
}

void module_real::write (const modulelist &list, bool modversions)
{
  std::string filename = name + ".mod.c";
  std::ofstream out (filename.c_str ());
  write_header (out);
  if (modversions)
    write_versions (out, list);
  write_depends (out, list);
  write_moddevtable (out);
}

module_real *module_real::open (const std::string &filename) throw (std::bad_alloc, std::runtime_error)
{
  Elf::file *file = Elf::file::open (filename.c_str ());
  switch (file->get_class ())
  {
    case Elf::file_class_32::id:
      return open_class<Elf::file_class_32> (filename, file);
    case Elf::file_class_64::id:
      return open_class<Elf::file_class_64> (filename, file);
    default:
      throw std::runtime_error ("Unsupported file class");
  }
}

template<typename Elf_class>
module_real *module_real::open_class (const std::string &filename, Elf::file *file) throw (std::bad_alloc, std::runtime_error)
{
  switch (file->get_data ())
  {
    case Elf::file_data_2LSB::id:
      return new module_data<Elf_class, Elf::file_data_2LSB> (filename, file);
    case Elf::file_data_2MSB::id:
      return new module_data<Elf_class, Elf::file_data_2MSB> (filename, file);
    default:
      throw std::runtime_error ("Unsupported data encoding");
  }
}

void module_real::read_modinfo (Elf::section *section) throw (std::runtime_error)
{
  const char *act, *end, *temp1, *temp2;
  act = static_cast <const char *> (section->_mem ());
  end = act + section->get_size ();
  while (act <= end)
  {
    temp1 = act;
    for (; *act && *act != '=' && act <= end; act++);
    if (act > end)
      break;
    temp2 = ++act;
    for (; *act && act <= end; act++);
    if (act > end)
      break;
    modinfo.insert (std::pair<std::string, std::string> (std::string (temp1, temp2 - temp1 - 1), std::string (temp2, act - temp2)));
    for (; !*act && act <= end; act++);
  }
}

void module_real::read_symtab (Elf::section_type<Elf::section_type_SYMTAB> *section) throw (std::runtime_error)
{
  for (std::vector<Elf::symbol *>::const_iterator it = section->get_symbols ().begin (); it != section->get_symbols ().end (); ++it)
  {
    Elf::symbol *symbol = *it;
    std::string symname = symbol->get_name_string ();

    switch (symbol->get_shndx ())
    {
      case SHN_COMMON:
        std::clog << "*** Warning: \"" << symname << "\" [" << name << "] is COMMON symbol" << std::endl;
        break;
      case SHN_ABS:
        if (symname.compare (0, symbol_prefix_crc.size (), symbol_prefix_crc) == 0)
        {
          std::string symname_real (symname.substr (symbol_prefix_crc.size ()));
          std::map<std::string, symbol_exported>::iterator it = symbols_exported.find (symname_real);
          if (it == symbols_exported.end ())
            symbols_exported.insert (std::pair<std::string, symbol_exported> (symname_real, symbol_exported (symname_real, symbol->get_value ())));
          else
            it->second.set_crc (symbol->get_value ());
        }
        break;
      case SHN_UNDEF:
        if (symbol->get_bind () != STB_GLOBAL &&
            symbol->get_bind () != STB_WEAK)
          break;
        //FIXME: if (symbol->get_type () == STT_REGISTER)
        //  break;
        /* ignore global offset table */
        if (symname == "_GLOBAL_OFFSET_TABLE_")
          break;
        /* ignore __this_module, it will be resolved shortly */
        if (symname == "__this_module")
          break;
        symbols_undefined.insert (std::pair<std::string, symbol_undefined> (symname, symbol_undefined (symname, symbol->get_bind () == STB_WEAK)));
        break;
      default:
        if (symname.compare (0, symbol_prefix_ksymtab.size (), symbol_prefix_ksymtab) == 0)
        {
          std::string symname_real (symname.substr (symbol_prefix_ksymtab.size ()));
          std::map<std::string, symbol_exported>::iterator it = symbols_exported.find (symname_real);
          if (it == symbols_exported.end ())
            symbols_exported.insert (std::pair<std::string, symbol_exported> (symname_real, symbol_exported (symname_real)));
        }
        else if (symname == symbol_name_cleanup)
          has_cleanup = true;
        else if (symname == symbol_name_init)
          has_init = true;
        break;
    };
  }
}

void module_real::write_depends (std::ostream &out, const modulelist &list)
{
  std::set<std::string> depends;
  for (std::map<std::string, symbol_undefined>::const_iterator it = symbols_undefined.begin (); it != symbols_undefined.end (); ++it)
  {
    try
    {
      const std::string &mod (list.get_module_name_short_for_symbol (it->first));
      if (mod != "vmlinux")
        depends.insert (mod);
    }
    catch (std::out_of_range &)
    { }
  }
  out <<
    "static const char __module_depends[]\n"
    "__attribute_used__\n"
    "__attribute__((section(\".modinfo\"))) =\n"
    "\"depends=";
  if (depends.begin () != depends.end ())
  {
    std::set<std::string>::const_iterator it = depends.begin ();
    out << *it;
    for (++it; it != depends.end (); ++it)
      out << ',' << *it;
  }
  out << "\";\n\n";
}

void module_real::write_header (std::ostream &out)
{
  out <<
    "#include <linux/module.h>\n"
    "#include <linux/vermagic.h>\n"
    "#include <linux/compiler.h>\n"
    "\n"
    "MODULE_INFO(vermagic, VERMAGIC_STRING);\n"
    "\n"
    "struct module __this_module\n"
    "__attribute__((section(\".gnu.linkonce.this_module\"))) = {\n"
    " .name = KBUILD_MODNAME,\n";
  if (has_init)
    out << " .init = init_module,\n";
  if (has_cleanup)
    out <<
      "#ifdef CONFIG_MODULE_UNLOAD\n"
      " .exit = cleanup_module,\n"
      "#endif\n";
  out << "};\n\n";
}

void module_real::write_moddevtable (std::ostream &out)
{
  for (std::list<module_devicetable::table_base *>::iterator it = devicetables.begin (); it != devicetables.end (); ++it)
  {
    module_devicetable::table_base *ent = *it;
    if (ent)
      ent->write (out);
  }
}

void module_real::write_versions (std::ostream &out, const modulelist &list)
{
  out <<
    "static const struct modversion_info ____versions[]\n"
    "__attribute_used__\n"
    "__attribute__((section(\"__versions\"))) = {\n";

  for (_symbols_undefined::const_iterator it = symbols_undefined.begin (); it != symbols_undefined.end (); ++it)
  {
    try
    {
      const symbol_exported &sym (list.get_symbol (it->first));
      if (sym.get_crc_valid ())
        out << "\t{ 0x" << std::hex << sym.get_crc () << std::dec << ", \"" << it->first << "\" },\n";
      else
        std::clog << "*** Warning: \"" << sym.get_name () << "\" [" << name << "] has no CRC!" << std::endl;
    }
    catch (std::out_of_range &)
    { 
      if (list.report_symbols_missing)
        std::clog << "*** Warning: \"" << it->first << "\" is undefined!" << std::endl;
    }
  }

  out << "};\n\n";
}

template <typename Elf_class, typename Elf_data>
module_data<Elf_class, Elf_data>::module_data (const std::string &filename, Elf::file *file) throw (std::runtime_error)
: module_real (filename, file)
{
  module_devicetable::table_create<Elf_class, Elf_data> (devicetables, this, file);
}

modulelist::modulelist () throw ()
: report_symbols_missing (false)
{ }

modulelist::~modulelist () throw ()
{
  for (_modules_real::iterator it = modules_real.begin (); it != modules_real.end (); ++it)
    delete it->second;
  for (_modules_shadow::iterator it = modules_shadow.begin (); it != modules_shadow.end (); ++it)
    delete it->second;
}

void modulelist::dump_read (const std::string &filename) throw (std::runtime_error)
{
  std::ifstream in (filename.c_str ());
  while (in.good ())
  {
    char buf[512];
    in.getline (buf, sizeof (buf));
    std::stringstream str (buf);
    uint32_t crc;
    std::string symbol, module_name;
    str >> std::hex >> crc >> std::dec >> symbol >> module_name;
    _modules_shadow::const_iterator it = modules_shadow.find (module_name);
    module *mod;
    if (it == modules_shadow.end ())
    {
      mod = new module (module_name);
      modules_shadow.insert (_modules_shadow_pair (module_name, mod));
    }
    else
      mod = it->second;
    mod->symbols_exported.insert (std::pair<std::string, symbol_exported> (symbol, symbol_exported (symbol, crc)));
    symbols_exported.insert (std::pair<std::string, std::string> (symbol, module_name));
    if (mod->get_is_vmlinux ())
      report_symbols_missing = true;
  }
}

void modulelist::dump_write (const std::string &filename) const throw (std::runtime_error)
{
  char buf[128];
  std::ofstream out (filename.c_str (), std::ios::trunc);

  for (_symbols::const_iterator it = symbols_exported.begin (); it != symbols_exported.end (); ++it)
  {
    const module *mod = get_module (it->second);
    const symbol_exported &sym = get_symbol (it->first);
    snprintf (buf, sizeof (buf), "0x%08x\t%s\t%s\n", sym.get_crc (), it->first.c_str (), mod->get_name ().c_str ());
    out << buf;
  }
}

const module *modulelist::get_module (const std::string &name) const throw (std::out_of_range)
{
  _modules_real::const_iterator it1 = modules_real.find (name);
  if (it1 != modules_real.end ())
    return it1->second;
  _modules_shadow::const_iterator it2 = modules_shadow.find (name);
  if (it2 != modules_shadow.end ())
    return it2->second;
  throw std::out_of_range ("Don't find module");
}

const module *modulelist::get_module_for_symbol (const symbolname &name) const throw (std::out_of_range)
{
  _symbols::const_iterator it = symbols_exported.find (name);
  if (it == symbols_exported.end ())
    throw std::out_of_range ("symbol is undefined");
  return get_module (it->second);
}

const std::string &modulelist::get_module_name_short_for_symbol (const symbolname &name) const throw (std::out_of_range)
{
  const module *mod = get_module_for_symbol (name);
  return mod->get_name_short ();
}

const symbol_exported &modulelist::get_symbol (const symbolname &name) const throw (std::out_of_range)
{
  const module *mod = get_module_for_symbol (name);
  std::map<std::string, symbol_exported>::const_iterator it = mod->get_symbols_exported ().find (name);
  if (it == mod->get_symbols_exported ().end ())
    throw std::logic_error ("Don't find symbol");
  return it->second;
}

void modulelist::insert (module_real *mod) throw (std::runtime_error)
{
  bool overwrite = false;

  if (mod->get_is_vmlinux ())
  {
    if (!modules_shadow.insert (_modules_shadow_pair (mod->get_name (), mod)).second)
      overwrite = true;
    report_symbols_missing = true;
  }
  else
  {
    if (!modules_real.insert (_modules_real_pair (mod->get_name (), mod)).second)
      throw std::runtime_error ("Already know a module with this name");
  }

  for (std::map<std::string, symbol_exported>::const_iterator it = mod->get_symbols_exported ().begin ();
       it != mod->get_symbols_exported ().end (); ++it)
    if (!symbols_exported.insert (std::pair<std::string, std::string> (it->second.get_name (), mod->get_name ())).second)
      if (!overwrite)
        std::clog << "*** Warning: \"" << it->second.get_name () << "\" [" << mod->get_name () << "] duplicated symbol!" << std::endl;
}

void modulelist::insert (const std::string &filename) throw (std::runtime_error)
{
  module_real *mod = module_real::open (filename);
  try
  {
    insert (mod);
  }
  catch (...)
  {
    delete mod;
    throw;
  }
}

void modulelist::write (bool modversions)
{
  for (_modules_real::iterator it = modules_real.begin (); it != modules_real.end (); ++it)
    it->second->write (*this, modversions);
}

symbol::symbol (const symbolname &name) throw ()
: name (name)
{ }

symbol_exported::symbol_exported (const symbolname &name) throw ()
: symbol (name), crc_valid (false)
{ }

symbol_exported::symbol_exported (const symbolname &name, uint32_t crc) throw ()
: symbol (name), crc (crc), crc_valid (true)
{ }

void symbol_exported::set_crc (uint32_t _crc) throw ()
{
  crc = _crc;
  crc_valid = true;
}

symbol_undefined::symbol_undefined (const symbolname &name, bool weak) throw ()
: symbol (name), weak (weak)
{ }

