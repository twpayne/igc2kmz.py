OLC2002=contrib/leonardo/olc2002
IGC2KMZ=./igc2kmz.py

CC=gcc
CFLAGS=-O2

SRCS=contrib/leonardo/olc2002.c
OBJS=$(SRCS:%.c=%.o)
BINS=$(OLC2002)
LIBS=-lm

.PHONY: all clean


all: $(BINS)

$(OLC2002): contrib/leonardo/olc2002.o
contrib/leonardo/olc2002.o: contrib/leonardo/olc2002.c

clean:
	rm -f $(BINS) $(OBJS)

%.o: %.c
	$(CC) -c -o $@ $(CFLAGS) $<

%: %.o
	$(CC) -o $@ $(CFLAGS) $^ $(LIBS)

EXAMPLES=examples/2008-07-28-XPG-KVE-02.kmz examples/858umbh1.kmz examples/2007-04-22-FLY-5094-01.kmz
.PRECIOUS: $(EXAMPLES:%.kmz=%.olc)

examples: $(EXAMPLES)

examples/2007-04-22-FLY-5094-01.kmz: examples/2007-04-22-FLY-5094-01.igc examples/2007-04-22-FLY-5094-01.gpx
	$(IGC2KMZ) -z 2 -o $@ \
		-i $< \
		-x examples/2007-04-22-FLY-5094-01.gpx \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_7967.jpg \
			-d "Nice cloud above the Pointe de Plate (2554m)" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_7977.jpg \
			-d "On the transition from Varan to the Aravis" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_7986.jpg \
			-d "Climbing to the north of the Quatre Tetes (2364m)" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8000.jpg \
			-d "Following Damien towards the Col des Aravis (where he started his flight)" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8012.jpg \
			-d "The cloud over the Tete Pelouse (2539m) is now within reach" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8023.jpg \
			-d "Having crossed the col the next target is the Tournette (2351m) which has a perfect cloud waiting for us!" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8029.jpg \
			-d "A picture of perfection!" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8068.jpg \
			-d "How perfect is that cloud\? I think it looks a bit like a rabbit (with a minature elephant on it's back)" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8087.jpg \
			-d "Passing Faverge on my left" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8099.jpg \
			-d "After Tom and I finish climbing above Charvin we decide to divert to avoid the development to the north east" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8107.jpg \
			-d "No photos for 40 minutes because of the concentration I needed to find a climb and also because we got rained on by the cloud!" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8109.jpg \
			-d "Following Lucas home to the Chamonix Valley" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8145.jpg \
			-d "Wow!" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8170.jpg \
			-d "Looking over at the Mer de Glace at the Aiguille Verte (4102m) with its nose in the clouds"

examples/2008-07-28-XPG-KVE-02.kmz: examples/2008-07-28-XPG-KVE-02.igc examples/2008-07-28-XPG-KVE-02.gpx

examples/858umbh1.kmz: examples/858umbh1.igc examples/858umbh1.gpx
	$(IGC2KMZ) -z 2 -o $@ \
		-i $< \
		-n "Martin Bühler" \
		-g "UP Edge" \
		-x examples/858umbh1.gpx

%.kmz: %.igc
	@echo "  IGC2KMZ $<"
	@./igc2kmz.py -z 2 -o $@ -i $< -x $*.gpx

%.gpx: %.olc
	bin/olc2gpx.py $< > $@

%.olc: %.igc $(OLC2002)
	$(OLC2002) $< > $@
