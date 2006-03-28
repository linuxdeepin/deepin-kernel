/*
 * module_devicetable_impl_2_6_16.cpp
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

#include "module_devicetable_impl_2_6_16.hpp"

#include <cstdio>
#include <stdint.h>
#include <sstream>

using namespace linuxkernel::module_devicetable;

std::ostream &operator << (std::ostream &out, const identifier_value<uint8_t> &id) throw ()
{
  char buf[4];
  snprintf (buf, sizeof (buf), "%02X", id.value);
  out << buf;
  return out;
}

std::ostream &operator << (std::ostream &out, const identifier_value<uint16_t> &id) throw ()
{
  char buf[8];
  snprintf (buf, sizeof (buf), "%04X", id.value);
  out << buf;
  return out;
}

std::ostream &operator << (std::ostream &out, const identifier_value<uint32_t> &id) throw ()
{
  char buf[12];
  snprintf (buf, sizeof (buf), "%08X", id.value);
  out << buf;
  return out;
}

table_entry_version<device_ccw, version_2_6_16>::table_entry_version () throw () :
  cu_type ("t"),
  dev_type ("m"),
  cu_model ("dt"),
  dev_model ("dm")
{ }

void table_entry_version<device_ccw, version_2_6_16>::write (std::ostream &out) const throw (std::runtime_error)
{
  out << "ccw:";
  cu_type.write (out, match_flags & CCW_DEVICE_ID_MATCH_CU_TYPE);
  cu_model.write (out, match_flags & CCW_DEVICE_ID_MATCH_CU_MODEL);
  dev_type.write (out, match_flags & CCW_DEVICE_ID_MATCH_DEVICE_TYPE);
  dev_model.write (out, match_flags & CCW_DEVICE_ID_MATCH_DEVICE_TYPE);
}

table_entry_version<device_ieee1394, version_2_6_16>::table_entry_version () throw () :
  vendor_id ("ven"),
  model_id ("mo"),
  specifier_id ("sp"),
  version ("ver")
{ }

void table_entry_version<device_ieee1394, version_2_6_16>::write (std::ostream &out) const throw (std::runtime_error)
{
  out << "ieee1394:";
  vendor_id.write (out, match_flags & IEEE1394_MATCH_VENDOR_ID);
  model_id.write (out, match_flags & IEEE1394_MATCH_MODEL_ID);
  specifier_id.write (out, match_flags & IEEE1394_MATCH_SPECIFIER_ID);
  version.write (out, match_flags & IEEE1394_MATCH_VERSION, true);
}

table_entry_version<device_pci, version_2_6_16>::table_entry_version () throw () :
  vendor ("v"),
  device ("d"),
  subvendor ("sv"),
  subdevice ("sd")
{ }

void table_entry_version<device_pci, version_2_6_16>::write (std::ostream &out) const throw (std::runtime_error)
{
  out << "pci:";
  vendor.write (out, vendor != PCI_ANY_ID);
  device.write (out, device != PCI_ANY_ID);
  subvendor.write (out, subvendor != PCI_ANY_ID);
  subdevice.write (out, subdevice != PCI_ANY_ID);

  identifier<uint8_t> baseclass ("bc", class_id >> 16);
  identifier_value<uint8_t> baseclass_mask (class_mask >> 16);
  identifier<uint8_t> subclass ("sc", class_id >> 8);
  identifier_value<uint8_t> subclass_mask (class_mask >> 8);
  identifier<uint8_t> interface ("i", class_id);
  identifier_value<uint8_t> interface_mask (class_mask);

  if ((baseclass_mask != 0 && baseclass_mask != 0xFF) ||
      (subclass_mask != 0 && subclass_mask != 0xFF) ||
      (interface_mask != 0 && interface_mask != 0xFF))
    throw std::runtime_error ("Can't handle masks");

  baseclass.write (out, baseclass_mask == 0xFF);
  subclass.write (out, subclass_mask == 0xFF);
  interface.write (out, interface_mask == 0xFF, true);
}

void table_entry_version<device_pnp, version_2_6_16>::write (std::ostream &out) const throw (std::runtime_error)
{
  out << "pnp:" << str << '*';
}

void table_entry_version<device_pnp_card, version_2_6_16>::write (std::ostream &out) const throw (std::runtime_error)
{
  out << "pnp:" << str << '*';
}

table_entry_version<device_usb, version_2_6_16>::table_entry_version () throw () :
  idVendor ("v"),
  idProduct ("p"),
  bDeviceClass ("dc"),
  bDeviceSubClass ("dsc"),
  bDeviceProtocol ("dp"),
  bInterfaceClass ("ic"),
  bInterfaceSubClass ("isc"),
  bInterfaceProtocol ("ip")
{ }

void table_entry_version<device_usb, version_2_6_16>::write (std::ostream &out) const throw (std::runtime_error)
{
  if (!idVendor && !bDeviceClass && !bInterfaceClass)
    return;

  out << "usb:";
  idVendor.write (out, match_flags & USB_DEVICE_ID_MATCH_VENDOR);
  idProduct.write (out, match_flags & USB_DEVICE_ID_MATCH_PRODUCT);
  out << 'd';
  if (bcdDevice_initial_digits)
  {
    char buf[12];
    snprintf (buf, sizeof (buf), "%0*X", bcdDevice_initial_digits, bcdDevice_initial);
    out << buf;
  }
  if (range_lo == range_hi)
    out << static_cast<int> (range_lo);
  else if (range_lo > 0 || range_hi < 9)
    out << '[' << static_cast<int> (range_lo) << '-' << static_cast<int> (range_hi) << ']';
  if (bcdDevice_initial_digits < 3)
    out << '*';
  bDeviceClass.write (out, match_flags & USB_DEVICE_ID_MATCH_DEV_CLASS);
  bDeviceSubClass.write (out, match_flags & USB_DEVICE_ID_MATCH_DEV_SUBCLASS);
  bDeviceProtocol.write (out, match_flags & USB_DEVICE_ID_MATCH_DEV_PROTOCOL);
  bInterfaceClass.write (out, match_flags & USB_DEVICE_ID_MATCH_INT_CLASS);
  bInterfaceSubClass.write (out, match_flags & USB_DEVICE_ID_MATCH_INT_SUBCLASS);
  bInterfaceProtocol.write (out, match_flags & USB_DEVICE_ID_MATCH_INT_PROTOCOL, true);
}

#define _do_convert(name) name = Elf::convert<Elf_data, typeof (id.name)> () (id.name)

template<typename Elf_class, typename Elf_data>
table_entry_data<device_ccw, version_2_6_16, Elf_class, Elf_data>::table_entry_data (const device_id<device_ccw, Elf_class> &id) throw ()
{
  _do_convert (match_flags);
  _do_convert (cu_type);
  _do_convert (dev_type);
  _do_convert (cu_model);
  _do_convert (dev_model);
}

template<typename Elf_class, typename Elf_data>
table_entry_data<device_ieee1394, version_2_6_16, Elf_class, Elf_data>::table_entry_data (const device_id<device_ieee1394, Elf_class> &id) throw ()
{
  _do_convert (match_flags);
  _do_convert (vendor_id);
  _do_convert (model_id);
  _do_convert (specifier_id);
  _do_convert (version);
}

template<typename Elf_class, typename Elf_data>
table_entry_data<device_pci, version_2_6_16, Elf_class, Elf_data>::table_entry_data (const device_id<device_pci, Elf_class> &id) throw ()
{
  _do_convert (vendor);
  _do_convert (device);
  _do_convert (subvendor);
  _do_convert (subdevice);
  _do_convert (class_id);
  _do_convert (class_mask);
}

template<typename Elf_class, typename Elf_data>
table_entry_data<device_pnp, version_2_6_16, Elf_class, Elf_data>::table_entry_data (const device_id<device_pnp, Elf_class> &id) throw ()
{
  std::stringstream s;
  s << 'd';
  s << static_cast <const char *> (static_cast <const void *> (id.id));
  str = s.str ();
}

template<typename Elf_class, typename Elf_data>
table_entry_data<device_pnp_card, version_2_6_16, Elf_class, Elf_data>::table_entry_data (const device_id<device_pnp_card, Elf_class> &id) throw ()
{
  std::stringstream s;
  s << 'c';
  s << static_cast <const char *> (static_cast <const void *> (id.id));
  for (int i = 0; i < PNP_MAX_DEVICES; i++)
  {
    if (! *id.devs[i].id)
      break;
    s << 'd';
    s << static_cast <const char *> (static_cast <const void *> (id.devs[i].id));
  }
  str = s.str ();
}

template<typename Elf_class, typename Elf_data>
table_entry_data<device_usb, version_2_6_16, Elf_class, Elf_data>::table_entry_data (const device_id<device_usb, Elf_class> &id, uint16_t _bcdDevice_initial, int _bcdDevice_initial_digits, unsigned char _range_lo, unsigned char _range_hi) throw ()
{
  _do_convert (match_flags);
  _do_convert (idVendor);
  _do_convert (idProduct);
  _do_convert (bDeviceClass);
  _do_convert (bDeviceSubClass);
  _do_convert (bDeviceProtocol);
  _do_convert (bInterfaceClass);
  _do_convert (bInterfaceSubClass);
  _do_convert (bInterfaceProtocol);
  bcdDevice_initial = _bcdDevice_initial;
  bcdDevice_initial_digits = _bcdDevice_initial_digits;
  range_lo = _range_lo;
  range_hi = _range_hi;
}

template<typename Elf_class, typename Elf_data>
void table_entry_data<device_usb, version_2_6_16, Elf_class, Elf_data>::add (const device_id<device_usb, Elf_class> &id, std::list<table_entry *> &table) throw ()
{
  uint16_t match_flags;
  uint16_t idVendor;
  uint16_t bcdDevice_lo = 0;
  uint16_t bcdDevice_hi = ~0;
  uint8_t bDeviceClass;
  uint8_t bInterfaceClass;

  _do_convert (match_flags);
  _do_convert (idVendor);
  if (match_flags & USB_DEVICE_ID_MATCH_DEV_LO)
    _do_convert (bcdDevice_lo);
  if (match_flags & USB_DEVICE_ID_MATCH_DEV_HI)
    _do_convert (bcdDevice_hi);
  _do_convert (bDeviceClass);
  _do_convert (bInterfaceClass);

  if (!(idVendor | bDeviceClass | bInterfaceClass))
    return;

  for (int ndigits = 3; bcdDevice_lo <= bcdDevice_hi; ndigits--)
  {
    unsigned char clo = bcdDevice_lo & 0xf;
    unsigned char chi = bcdDevice_hi & 0xf;

    if (chi > 9)    /* it's bcd not hex */
      chi = 9;

    bcdDevice_lo >>= 4;
    bcdDevice_hi >>= 4;

    if (bcdDevice_lo == bcdDevice_hi || !ndigits)
    {
      table.push_back (new table_entry_data<device_usb, version_2_6_16, Elf_class, Elf_data> (id, bcdDevice_lo, ndigits, clo, chi));
      return;
    }

    if (clo > 0)
      table.push_back (new table_entry_data<device_usb, version_2_6_16, Elf_class, Elf_data> (id, bcdDevice_lo++, ndigits, clo, 9));

    if (chi < 9)
      table.push_back (new table_entry_data<device_usb, version_2_6_16, Elf_class, Elf_data> (id, bcdDevice_hi--, ndigits, 0, chi));
  }
}

template<typename device, typename Elf_class, typename Elf_data>
table_data<device, version_2_6_16, Elf_class, Elf_data>::table_data (const void *mem, size_t size) throw (std::runtime_error)
{
  if (size % sizeof (devin))
    throw std::runtime_error ("Bad size");
  size_t len = size / sizeof (devin);
  // Remove the terminator.
  len--;
  const devin *e = static_cast <const devin *> (mem);
  for (size_t i = 0; i < len; ++i)
    table_entry_data<device, version_2_6_16, Elf_class, Elf_data>::add (e[i], this->entries);
}

#define make_templates(name) \
template class table_data<name, version_2_6_16, Elf::file_class_32, Elf::file_data_2LSB>; \
template class table_data<name, version_2_6_16, Elf::file_class_32, Elf::file_data_2MSB>; \
template class table_data<name, version_2_6_16, Elf::file_class_64, Elf::file_data_2LSB>; \
template class table_data<name, version_2_6_16, Elf::file_class_64, Elf::file_data_2MSB>
make_templates(device_ccw);
make_templates(device_ieee1394);
make_templates(device_pci);
make_templates(device_pnp);
make_templates(device_pnp_card);
make_templates(device_usb);
