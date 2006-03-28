/*
 * module_devicetable_impl_2_6_16.hpp
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

#ifndef MODULE_DEVICETABLE_IMPL_2_6_16_HPP
#define MODULE_DEVICETABLE_IMPL_2_6_16_HPP

#include "module_devicetable.hpp"

#include "elf.hpp"

namespace 
{ 
  using namespace linuxkernel::module_devicetable;

  template<typename _class>
    struct _elfdef
    { };

  template<>
    struct _elfdef<Elf::file_class_32>
    {
      typedef uint32_t pointer;
    };

  template<>
    struct _elfdef<Elf::file_class_64>
    { 
      typedef uint64_t pointer;
    };

  template<typename device, typename Elf_class>
    struct device_id
    { };

  template<typename Elf_class>
    struct device_id<device_ccw, Elf_class>
    {
      uint16_t match_flags;
      uint16_t cu_type;
      uint16_t dev_type;
      uint8_t cu_model;
      uint8_t dev_model;
      typename _elfdef<Elf_class>::pointer driver_info;
    };

  enum
  {
    CCW_DEVICE_ID_MATCH_CU_TYPE = 0x01,
    CCW_DEVICE_ID_MATCH_CU_MODEL = 0x02,
    CCW_DEVICE_ID_MATCH_DEVICE_TYPE = 0x04,
    CCW_DEVICE_ID_MATCH_DEVICE_MODEL = 0x08,
  };

  template<typename Elf_class>
    struct device_id<device_i2c, Elf_class>
    {
      uint16_t id;
    };

  template<typename Elf_class>
    struct device_id<device_ieee1394, Elf_class>
    {
      uint32_t match_flags;
      uint32_t vendor_id;
      uint32_t model_id;
      uint32_t specifier_id;
      uint32_t version;
      typename _elfdef<Elf_class>::pointer driver_info;
    };

  enum
  {
    IEEE1394_MATCH_VENDOR_ID = 0x0001,
    IEEE1394_MATCH_MODEL_ID = 0x0002,
    IEEE1394_MATCH_SPECIFIER_ID = 0x0004,
    IEEE1394_MATCH_VERSION = 0x0008,
  };

  template<typename Elf_class>
    struct device_id<device_pci, Elf_class>
    {
      uint32_t vendor, device;
      uint32_t subvendor, subdevice;
      uint32_t class_id, class_mask;
      typename _elfdef<Elf_class>::pointer driver_info;
    };

  const unsigned int PCI_ANY_ID = ~0U;
  const int PNP_ID_LEN = 8;
  const int PNP_MAX_DEVICES = 8;

  template <typename Elf_class>
    struct device_id<device_pnp, Elf_class>
    {
      uint8_t id[PNP_ID_LEN];
      typename _elfdef<Elf_class>::pointer driver_info;
    };

  template <typename Elf_class>
    struct device_id<device_pnp_card, Elf_class>
    {
      uint8_t id[PNP_ID_LEN];
      typename _elfdef<Elf_class>::pointer driver_info;
      struct
      {
        uint8_t id[PNP_ID_LEN];
      }
      devs[PNP_MAX_DEVICES];
    };

  template <typename Elf_class>
    struct device_id<device_serio, Elf_class>
    {
      uint8_t type;
      uint8_t extra;
      uint8_t id;
      uint8_t proto;
    };

  enum
  {
    SERIO_DEVICE_ID_ANY = 0xff,
  };

  template <typename Elf_class>
    struct device_id<device_usb, Elf_class>
    {
      uint16_t match_flags;
      uint16_t idVendor;
      uint16_t idProduct;
      uint16_t bcdDevice_lo;
      uint16_t bcdDevice_hi;
      uint8_t bDeviceClass;
      uint8_t bDeviceSubClass;
      uint8_t bDeviceProtocol;
      uint8_t bInterfaceClass;
      uint8_t bInterfaceSubClass;
      uint8_t bInterfaceProtocol;
      typename _elfdef<Elf_class>::pointer driver_info;
    };

  enum
  {
    USB_DEVICE_ID_MATCH_VENDOR = 0x0001,
    USB_DEVICE_ID_MATCH_PRODUCT = 0x0002,
    USB_DEVICE_ID_MATCH_DEV_LO = 0x0004,
    USB_DEVICE_ID_MATCH_DEV_HI = 0x0008,
    USB_DEVICE_ID_MATCH_DEV_CLASS = 0x0010,
    USB_DEVICE_ID_MATCH_DEV_SUBCLASS = 0x0020,
    USB_DEVICE_ID_MATCH_DEV_PROTOCOL = 0x0040,
    USB_DEVICE_ID_MATCH_INT_CLASS = 0x0080,
    USB_DEVICE_ID_MATCH_INT_SUBCLASS = 0x0100,
    USB_DEVICE_ID_MATCH_INT_PROTOCOL = 0x0200,
  };

  template<typename type>
    class identifier_value
    {
      public:
        type value;

        identifier_value () : value (0) { }
        identifier_value (const type &value) : value (value) { }
        const type &operator = (const type &_value) { value = _value; return value; }
        bool operator ! () const { return !value; }
        operator type () const { return value; }
        template<typename Elf_data>
          void set (const type _value)
          { value = Elf::convert<Elf_data, type> () (_value); }
    };

  template<typename type>
    class identifier
    {
      public:
        identifier_value<type> value;
        std::string sep;

        identifier (const std::string &sep) : sep (sep) { }
        identifier (const std::string &sep, const type &value) : value (value), sep (sep) { }
        const type &operator = (const type &_value) { value = _value; return value.value; }
        bool operator ! () const { return !value; }
        operator type () const { return value; }
        void write (std::ostream &out, bool enable, bool last = false) const
        {
          out << sep;
          if (enable)
          {
            out << value;
            if (last)
              out << '*';
          }
          else
            out << '*';
        }
    };
}

std::ostream &operator << (std::ostream &out, const identifier_value<uint8_t> &id) throw ();
std::ostream &operator << (std::ostream &out, const identifier_value<uint16_t> &id) throw ();
std::ostream &operator << (std::ostream &out, const identifier_value<uint32_t> &id) throw ();

namespace linuxkernel
{
  namespace module_devicetable
  {
    template<>
      class table_entry_version<device_ccw, version_2_6_16> : public table_entry
      {
        public:
          table_entry_version () throw ();
          void write (std::ostream &) const throw (std::runtime_error);

          identifier_value<uint16_t> match_flags;
          identifier<uint16_t> cu_type;
          identifier<uint16_t> dev_type;
          identifier<uint8_t> cu_model;
          identifier<uint8_t> dev_model;
      };

    template<typename Elf_class, typename Elf_data>
      class table_entry_data<device_ccw, version_2_6_16, Elf_class, Elf_data> : public table_entry_version<device_ccw, version_2_6_16>
      {
        protected:
          table_entry_data (const device_id<device_ccw, Elf_class> &) throw ();

        public:
          static void add (const device_id<device_ccw, Elf_class> &id, std::list<table_entry *> &table) throw ()
          {
            table.push_back (new table_entry_data<device_ccw, version_2_6_16, Elf_class, Elf_data> (id));
          }
      };

    template<>
      class table_entry_version<device_ieee1394, version_2_6_16> : public table_entry
      {
        public:
          table_entry_version () throw ();
          void write (std::ostream &) const throw (std::runtime_error);

          identifier_value<uint32_t> match_flags;
          identifier<uint32_t> vendor_id;
          identifier<uint32_t> model_id;
          identifier<uint32_t> specifier_id;
          identifier<uint32_t> version;
      };

    template<typename Elf_class, typename Elf_data>
      class table_entry_data<device_ieee1394, version_2_6_16, Elf_class, Elf_data> : public table_entry_version<device_ieee1394, version_2_6_16>
      {
        protected:
          table_entry_data (const device_id<device_ieee1394, Elf_class> &) throw ();

        public:
          static void add (const device_id<device_ieee1394, Elf_class> &id, std::list<table_entry *> &table) throw ()
          {
            table.push_back (new table_entry_data<device_ieee1394, version_2_6_16, Elf_class, Elf_data> (id));
          }
      };

    template<>
      class table_entry_version<device_pci, version_2_6_16> : public table_entry
      {
        public:
          table_entry_version () throw ();
          void write (std::ostream &) const throw (std::runtime_error);

          identifier<uint32_t> vendor, device;
          identifier<uint32_t> subvendor, subdevice;
          identifier_value<uint32_t> class_id, class_mask;
      };

    template<typename Elf_class, typename Elf_data>
      class table_entry_data<device_pci, version_2_6_16, Elf_class, Elf_data> : public table_entry_version<device_pci, version_2_6_16>
      {
        protected:
          table_entry_data (const device_id<device_pci, Elf_class> &) throw ();

        public:
          static void add (const device_id<device_pci, Elf_class> &id, std::list<table_entry *> &table) throw ()
          {
            table.push_back (new table_entry_data<device_pci, version_2_6_16, Elf_class, Elf_data> (id));
          }
      };

    template<>
      class table_entry_version<device_pnp, version_2_6_16> : public table_entry
      {
        public:
          void write (std::ostream &) const throw (std::runtime_error);

          std::string str;
      };

    template<typename Elf_class, typename Elf_data>
      class table_entry_data<device_pnp, version_2_6_16, Elf_class, Elf_data> : public table_entry_version<device_pnp, version_2_6_16>
      {
        protected:
          table_entry_data (const device_id<device_pnp, Elf_class> &) throw ();

        public:
          static void add (const device_id<device_pnp, Elf_class> &id, std::list<table_entry *> &table) throw ()
          {
            table.push_back (new table_entry_data<device_pnp, version_2_6_16, Elf_class, Elf_data> (id));
          }
      };

    template<>
      class table_entry_version<device_pnp_card, version_2_6_16> : public table_entry
      {
        public:
          void write (std::ostream &) const throw (std::runtime_error);

          std::string str;
      };

    template<typename Elf_class, typename Elf_data>
      class table_entry_data<device_pnp_card, version_2_6_16, Elf_class, Elf_data> : public table_entry_version<device_pnp_card, version_2_6_16>
      {
        protected:
          table_entry_data (const device_id<device_pnp_card, Elf_class> &) throw ();

        public:
          static void add (const device_id<device_pnp_card, Elf_class> &id, std::list<table_entry *> &table) throw ()
          {
            table.push_back (new table_entry_data<device_pnp_card, version_2_6_16, Elf_class, Elf_data> (id));
          }
      };

    template<>
      class table_entry_version<device_usb, version_2_6_16> : public table_entry
      {
        public:
          table_entry_version () throw ();
          void write (std::ostream &) const throw (std::runtime_error);

          identifier_value<uint16_t> match_flags;
          identifier<uint16_t> idVendor;
          identifier<uint16_t> idProduct;
          unsigned int bcdDevice_initial;
          int bcdDevice_initial_digits;
          unsigned char range_lo;
          unsigned char range_hi;
          identifier<uint8_t> bDeviceClass;
          identifier<uint8_t> bDeviceSubClass;
          identifier<uint8_t> bDeviceProtocol;
          identifier<uint8_t> bInterfaceClass;
          identifier<uint8_t> bInterfaceSubClass;
          identifier<uint8_t> bInterfaceProtocol;
      };

    template<typename Elf_class, typename Elf_data>
      class table_entry_data<device_usb, version_2_6_16, Elf_class, Elf_data> : public table_entry_version<device_usb, version_2_6_16>
      {
        protected:
          table_entry_data (const device_id<device_usb, Elf_class> &, uint16_t bcdDevice_initial, int bcdDevice_initial_digits, unsigned char range_lo, unsigned char range_hi) throw ();

        public:
          static void add (const device_id<device_usb, Elf_class> &, std::list<table_entry *> &table) throw ();
      };

    template<typename device, typename Elf_class, typename Elf_data>
      class table_data<device, version_2_6_16, Elf_class, Elf_data> : public table<device, Elf_class, Elf_data>
      {
        protected:
          typedef device_id<device, Elf_class> devin;

        public:
          table_data (const void *mem, size_t size) throw (std::runtime_error);
      };
  }
}

#endif
