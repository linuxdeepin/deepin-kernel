/*
 * endian.hpp
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

#ifndef ENDIAN_HPP
#define ENDIAN_HPP

#include <endian.h>
#include <stdint.h>

namespace endian
{
  class little_endian
  { };

  class big_endian
  { };

#if __BYTE_ORDER == __LITTLE_ENDIAN
  typedef little_endian host_endian;
#elif __BYTE_ORDER == __BIG_ENDIAN
  typedef big_endian host_endian;
#endif

  template <typename type>
    struct convert_nop
    {
      inline type operator () (const type &in) const throw () { return in; }
    };

  template <typename type>
    struct convert_simple
    { };

  template <>
    struct convert_simple<uint8_t> : public convert_nop<uint8_t>
    { };

  template <>
    struct convert_simple<uint16_t>
    {
      inline uint16_t operator () (const uint16_t &in) const throw ()
      {
        return (in & 0x00ffU) << 8 | 
          (in & 0xff00U) >> 8;
      }
    };

  template <>
    struct convert_simple<uint32_t>
    {
      inline uint32_t operator () (const uint32_t &in) const throw ()
      {
        return (in & 0x000000ffU) << 24 |
          (in & 0xff000000U) >> 24 |
          (in & 0x0000ff00U) << 8  |
          (in & 0x00ff0000U) >> 8;
      }
    };

  template <>
    struct convert_simple<uint64_t>
    {
      inline uint64_t operator () (const uint64_t &in) const throw ()
      {
        return (in & 0x00000000000000ffULL) << 56 |
          (in & 0xff00000000000000ULL) >> 56 |
          (in & 0x000000000000ff00ULL) << 40 |
          (in & 0x00ff000000000000ULL) >> 40 |
          (in & 0x0000000000ff0000ULL) << 24 |
          (in & 0x0000ff0000000000ULL) >> 24 |
          (in & 0x00000000ff000000ULL) << 8  |
          (in & 0x000000ff00000000ULL) >> 8;
      }
    };

  template <>
    struct convert_simple<const uint8_t> : public convert_simple<uint8_t>
    { };

  template <>
    struct convert_simple<const uint16_t> : public convert_simple<uint16_t>
    { };

  template <>
    struct convert_simple<const uint32_t> : public convert_simple<uint32_t>
    { };

  template <typename from, typename to, typename type>
    struct convert_complete
    { };

  template <typename type>
    struct convert_complete<little_endian, little_endian, type> : public convert_nop<type>
    { };

  template <typename type>
    struct convert_complete<little_endian, big_endian, type> : public convert_simple<type>
    { };

  template <typename type>
    struct convert_complete<big_endian, big_endian, type> : public convert_nop<type>
    { };

  template <typename type>
    struct convert_complete<big_endian, little_endian, type> : public convert_simple<type>
    { };

  template <typename from, typename type>
    struct convert
    { };

  template <typename type>
    struct convert<little_endian, type> : public convert_complete<little_endian, host_endian, type>
    { };

  template <typename type>
    struct convert<big_endian, type> : public convert_complete<big_endian, host_endian, type>
    { };
}

#endif
