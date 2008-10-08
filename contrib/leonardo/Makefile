CC=gcc
CFLAGS=-O2

SRCS=olc2002.c
OBJS=$(SRCS:%.c=%.o)
BINS=olc2002
LIBS=-lm

.PHONY: all clean

all: $(BINS)

olc2002: $(OBJS)

clean:
	@echo "  CLEAN   $(BINS) $(OBJS)"
	@rm -f $(BINS) $(OBJS)

%.o: %.c
	@echo "  CC      $<"
	@$(CC) -c -o $@ $(CFLAGS) $<

%: %.o
	@echo "  LD      $<"
	@$(CC) -o $@ $(CFLAGS) $^ $(LIBS)
