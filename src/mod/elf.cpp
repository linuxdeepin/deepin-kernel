/*
 * elf.cpp
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
#include "endian.hpp"

#include <stdexcept>

#include <fcntl.h>
#include <elf.h>
#include <sys/mman.h>
#include <sys/stat.h>

using namespace Elf;

namespace
{
  template <typename _class>
    struct _elfdef
    { };

  template <>
    struct _elfdef<file_class_32>
    {
      typedef Elf32_Ehdr Ehdr;
      typedef Elf32_Shdr Shdr;
      typedef Elf32_Sym Sym;
      static inline uint8_t st_bind (uint8_t st_info) throw () { return ELF32_ST_BIND (st_info); }
      static inline uint8_t st_type (uint8_t st_info) throw () { return ELF32_ST_TYPE (st_info); }
    };

  template <>
    struct _elfdef<file_class_64>
    {
      typedef Elf64_Ehdr Ehdr;
      typedef Elf64_Shdr Shdr;
      typedef Elf64_Sym Sym;
      static inline uint8_t st_bind (uint8_t st_info) throw () { return ELF64_ST_BIND (st_info); }
      static inline uint8_t st_type (uint8_t st_info) throw () { return ELF64_ST_TYPE (st_info); }
    };
}

file::file (const char *filename, void *mem, size_t len) throw (std::bad_alloc)
: filename (std::string (filename)), mem (mem), len (len)
{ }

file::~file () throw ()
{
  ::munmap (mem, len);
  for (std::vector<section *>::iterator it = sections.begin (); it != sections.end (); ++it)
    delete *it;
}

file *file::open (const char *filename) throw (std::bad_alloc, std::runtime_error)
{
  struct stat buf;
  int fd;
  void *mem;
  size_t len;
  if ((fd = ::open (filename, O_RDONLY)) == -1)
    throw std::runtime_error ("mapping failed");
  try
  {
    if (::fstat (fd, &buf) == -1)
      throw std::runtime_error ("mapping failed");
    len = buf.st_size;
    if ((mem = ::mmap (0, len, PROT_READ | PROT_WRITE, MAP_PRIVATE, fd, 0)) == MAP_FAILED)
      throw std::runtime_error ("mapping failed");

    const uint8_t *buf = static_cast <uint8_t *> (mem);

    switch (buf[EI_CLASS])
    {
      case ELFCLASS32:
        return open_class<file_class_32> (filename, buf, mem, len);
      case ELFCLASS64:
        return open_class<file_class_64> (filename, buf, mem, len);
      default:
        throw std::runtime_error ("Invalid file class");
    }
  }
  catch (...)
  {
    ::close (fd);
    throw;
  }
}

template<typename _class>
file *file::open_class (const char *filename, const uint8_t *buf, void * mem, size_t len) throw (std::bad_alloc, std::runtime_error)
{
  switch (buf[EI_DATA])
  {
    case ELFDATA2LSB:
      return new file_data<_class, file_data_2LSB> (filename, mem, len);
    case ELFDATA2MSB:
      return new file_data<_class, file_data_2MSB> (filename, mem, len);
    default:
      throw std::runtime_error ("Invalid file data");
  }
}

template <typename _class, typename _data>
file_data<_class, _data>::file_data (const char *filename) throw (std::bad_alloc, std::runtime_error)
: file (filename)
{ 
  construct ();
}

template <typename _class, typename _data>
file_data<_class, _data>::file_data (const char *filename, void *mem, size_t len) throw (std::bad_alloc, std::runtime_error)
: file (filename, mem, len)
{
  construct ();
}

template <typename _class, typename _data>
void file_data<_class, _data>::construct () throw (std::bad_alloc, std::runtime_error)
{
  uint8_t *buf = static_cast <uint8_t *> (this->mem);
  if (buf[EI_CLASS] != _class::id)
    throw std::runtime_error ("Wrong file class");
  if (buf[EI_DATA] != _data::id)
    throw std::runtime_error ("Wrong data encoding");

  typedef typename _elfdef<_class>::Ehdr Ehdr;
  Ehdr *ehdr = static_cast <Ehdr *> (this->mem);
  this->type     = convert<_data, typeof (ehdr->e_type    )> () (ehdr->e_type    );
  this->machine  = convert<_data, typeof (ehdr->e_machine )> () (ehdr->e_machine );
  this->shoff    = convert<_data, typeof (ehdr->e_shoff   )> () (ehdr->e_shoff   );
  this->shnum    = convert<_data, typeof (ehdr->e_shnum   )> () (ehdr->e_shnum   );
  this->shstrndx = convert<_data, typeof (ehdr->e_shstrndx)> () (ehdr->e_shstrndx);

  typedef typename _elfdef<_class>::Shdr Shdr;
  Shdr *shdrs = static_cast <Shdr *> (static_cast <void *> (static_cast <char *> (this->mem) + this->shoff));

  this->sections.reserve (this->shnum);

  for (unsigned int i = 0; i < this->shnum; i++)
  {
    section *temp;
    switch (convert<_data, typeof (shdrs[i].sh_type)> () (shdrs[i].sh_type))
    {
      case section_type_SYMTAB::id:
        temp = new section_real<_class, _data, section_type_SYMTAB> (&shdrs[i], this->mem);
        break;
      default:
        temp = new section_real<_class, _data, section_type_UNDEFINED> (&shdrs[i], this->mem);
        break;
    }
    this->sections.push_back (temp);
  }

  for (unsigned int i = 0; i < this->shnum; i++)
    this->sections[i]->update_string_table (this);
}

void section::update_string_table (file *file) throw (std::bad_alloc)
{
  const section *section = file->get_section (file->get_shstrndx ());
  this->name_string = std::string (static_cast <const char *> (section->_mem ()) + this->name);
}

template <typename _class, typename _data>
section_data<_class, _data>::section_data (void *header, void *mem) throw ()
{
  typedef typename _elfdef<_class>::Shdr Shdr;
  Shdr *shdr = static_cast <Shdr *> (header);
  this->name   = convert<_data, typeof (shdr->sh_name  )> () (shdr->sh_name  );
  this->type   = convert<_data, typeof (shdr->sh_type  )> () (shdr->sh_type  );
  this->offset = convert<_data, typeof (shdr->sh_offset)> () (shdr->sh_offset);
  this->size   = convert<_data, typeof (shdr->sh_size  )> () (shdr->sh_size  );
  this->link   = convert<_data, typeof (shdr->sh_link  )> () (shdr->sh_link  );
  this->mem = static_cast <void *> (static_cast <char *> (mem) + this->offset);
}

section_type<section_type_SYMTAB>::~section_type () throw ()
{
  for (std::vector<symbol *>::iterator it = symbols.begin (); it != symbols.end (); ++it)
    delete *it;
}

void section_type<section_type_SYMTAB>::update_string_table (file *file) throw (std::bad_alloc)
{
  section::update_string_table (file);
  for (unsigned int i = 0; i < symbols.size (); i++)
    this->symbols[i]->update_string_table (file, link);
}

template <typename _class, typename _data>
section_real<_class, _data, section_type_SYMTAB>::section_real (void *header, void *mem) throw (std::bad_alloc)
: section_data<_class, _data> (header, mem)
{
  if (this->type != SHT_SYMTAB)
    throw std::logic_error ("Wrong section type");
  typedef typename _elfdef<_class>::Sym Sym;
  Sym *syms = static_cast <Sym *> (this->mem);
  unsigned int max = this->size / sizeof (Sym);

  this->symbols.reserve (max);

  for (unsigned int i = 0; i < max; i++)
    this->symbols.push_back (new symbol_data<_class, _data> (&syms[i]));
}

template <typename _class, typename _data>
symbol_data<_class, _data>::symbol_data (void *mem) throw ()
{
  typedef typename _elfdef<_class>::Sym Sym;
  Sym *sym = static_cast <Sym *> (mem);
  this->name  = convert<_data, typeof (sym->st_name )> () (sym->st_name);
  this->info  = convert<_data, typeof (sym->st_info )> () (sym->st_info);
  this->shndx = convert<_data, typeof (sym->st_shndx)> () (sym->st_shndx);
  this->value = convert<_data, typeof (sym->st_value)> () (sym->st_value);
  this->size  = convert<_data, typeof (sym->st_size )> () (sym->st_size);
  this->bind = _elfdef<_class>::st_bind (this->info);
  this->type = _elfdef<_class>::st_type (this->info);
}

template <typename _class, typename _data>
void symbol_data<_class, _data>::update_string_table (file *file, uint16_t s) throw (std::bad_alloc)
{
  const section *section = file->get_section (s);
  this->name_string = std::string (static_cast <const char *> (section->_mem ()) + this->name);
}

