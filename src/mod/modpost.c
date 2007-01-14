#include <elf.h>
#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main (int argc, char *argv[])
{
  char const *data, *class;
  char prog[1024];
  unsigned char ei[EI_NIDENT];
  int opt;
  FILE *file;

  while ((opt = getopt (argc, argv, "ai:I:mo:w")) != -1)
  { 
    switch(opt)
    {
      case 'a':
      case 'i':
      case 'I':
      case 'm':
      case 'o':
      case 'w':
        break;
      default:
        return 1;
    }
  }

  if (!(file = fopen (argv[optind], "r")))
  {
    fprintf (stderr, "Can't open file\n");
    return 1;
  }
  if (fread (ei, 1, EI_NIDENT, file) != EI_NIDENT)
  {
    fprintf (stderr, "Error: input truncated\n");
    return 1;
  }
  if (memcmp (ei, ELFMAG, SELFMAG) != 0)
  {
    fprintf (stderr, "Error: not ELF\n");
    return 1;
  }
  switch (ei[EI_DATA]) {
    case ELFDATA2LSB:
      data = "lsb";
      break;
    case ELFDATA2MSB:
      data = "msb";
      break;
    default:
      return 1;
  }
  switch (ei[EI_CLASS]) {
    case ELFCLASS32:
      class = "32";
      break;
    case ELFCLASS64:
      class = "64";
      break;
    default:
      return 1;
  }
  snprintf (prog, sizeof prog, "%s.real-%s-%s", argv[0], data, class);

  return execv (prog, argv);
}
