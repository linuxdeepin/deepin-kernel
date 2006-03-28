/*
 * elf.hpp
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

#ifndef ELF_HPP
#define ELF_HPP

#include "endian.hpp"

#include <stdexcept>
#include <string>
#include <vector>

#include <stdint.h>

namespace Elf
{
  class file_class_32 { public: static const unsigned int id = 1; };
  class file_class_64 { public: static const unsigned int id = 2; };
  class file_data_2LSB { public: static const unsigned int id = 1; };
  class file_data_2MSB { public: static const unsigned int id = 2; };
  class section_type_UNDEFINED { };
  class section_type_SYMTAB { public: static const unsigned int id = 2; };

  class section;

  class file
  {
    public:
      virtual ~file () throw ();

      virtual const uint8_t get_class () const throw () = 0;
      virtual const uint8_t get_data () const throw () = 0;
      const uint16_t get_type () const throw () { return type; }
      const uint16_t get_machine () const throw () { return machine; }
      const uint16_t get_shstrndx () const throw () { return shstrndx; }

      const std::vector <section *> get_sections () const throw () { return sections; };
      const section *get_section (unsigned int i) const throw (std::out_of_range) { return sections.at(i); };

      const void *const _mem () const throw () { return mem; }

      static file *open (const char *filename) throw (std::bad_alloc, std::runtime_error);

    protected:
      file (const char *, void *, size_t len) throw (std::bad_alloc);

      template<typename _class>
        static file *open_class (const char *, const uint8_t *, void *, size_t) throw (std::bad_alloc, std::runtime_error);

      uint16_t type;
      uint16_t machine;
      uint64_t shoff;
      uint16_t shnum;
      uint16_t shstrndx;

      std::vector <section *> sections;

      const std::string filename;
      void *mem;
      size_t len;
  };

  template <typename _class, typename _data>
    class file_data : public file
    {
      public:
        file_data (const char *) throw (std::bad_alloc, std::runtime_error);
        file_data (const char *, void *, size_t len) throw (std::bad_alloc, std::runtime_error);

        const uint8_t get_class () const throw () { return _class::id; }
        const uint8_t get_data () const throw () { return _data::id; }

      private:
        void construct () throw (std::bad_alloc, std::runtime_error);
    };

  class section
  {
    public:
      virtual ~section () throw () {}

      uint32_t get_type () const throw () { return type; }
      uint64_t get_size () const throw () { return size; }
      const std::string &get_name_string () const throw () { return name_string; }

      const void *const _mem () const throw () { return mem; }

      virtual void update_string_table (file *) throw (std::bad_alloc);

    protected:
      uint32_t name;
      uint32_t type;
      uint64_t offset;
      uint64_t size;
      uint32_t link;

      std::string name_string;

      void *mem;
  };

  template <typename _class, typename _data>
    class section_data : public virtual section
    {
      public:
        section_data (void *, void *) throw ();
    };

  template <typename _type>
    class section_type : public virtual section
    {
    };

  class symbol;

  template <>
    class section_type<section_type_SYMTAB> : public virtual section
    {
      public:
        ~section_type () throw ();

        const std::vector<symbol *> &get_symbols () throw () { return symbols; }

        void update_string_table (file *) throw (std::bad_alloc);

      protected:
        std::vector<symbol *> symbols;
    };

  template <typename _class, typename _data, typename _type>
    class section_real : public section_data<_class, _data>, public section_type<_type>
    {
      public:
        section_real (void *, void *) throw ();
    };

  template <typename _class, typename _data>
    class section_real<_class, _data, section_type_UNDEFINED> : public section_data<_class, _data>, public section_type<section_type_UNDEFINED>
    {
      public:
        section_real (void *a, void *b) throw () : section_data<_class, _data> (a, b) { }
    };

  template <typename _class, typename _data>
    class section_real<_class, _data, section_type_SYMTAB> : public section_data<_class, _data>, public section_type<section_type_SYMTAB>
    {
      public:
        section_real (void *, void *) throw (std::bad_alloc);
    };

  class symbol
  {
    public:
      virtual ~symbol () throw () {}

      uint8_t get_info () const throw () { return info; }
      uint16_t get_shndx () const throw () { return shndx; }
      uint64_t get_value () const throw () { return value; }
      uint64_t get_size () const throw () { return size; }
      uint8_t get_bind () const throw () { return bind; }
      uint8_t get_type () const throw () { return type; }
      const std::string &get_name_string () const throw () { return name_string; }

      virtual void update_string_table (file *, uint16_t) throw (std::bad_alloc) = 0;

    protected:
      uint32_t name;
      uint8_t info;
      uint16_t shndx;
      uint64_t value;
      uint64_t size;
      uint8_t bind;
      uint8_t type;

      std::string name_string;
  };

  template <typename _class, typename _data>
    class symbol_data : public symbol
    {
      public:
        symbol_data (void *) throw ();

        void update_string_table (file *, uint16_t) throw (std::bad_alloc);

      protected:
    };

  template <typename from, typename type>
    struct convert
    { };

  template <typename type>
    struct convert<file_data_2LSB, type> : public endian::convert<endian::little_endian, type>
    { };

  template <typename type>
    struct convert<file_data_2MSB, type> : public endian::convert<endian::big_endian, type>
    { };
}

#endif
