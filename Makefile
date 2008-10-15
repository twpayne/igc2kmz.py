OLC2002=contrib/leonardo/olc2002
IGC2KMZ=bin/igc2kmz.py
IGC2TASK=bin/igc2task.py
BRAND2KML=bin/brand2kml.py

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

EXAMPLES=examples/2008-07-28-XPG-KVE-02.kmz \
	 examples/2008-06-07-FLY-6113-01.kmz \
	 examples/2008-06-16-xgd-001-01.kmz \
	 examples/2008-09-05-CGP-XAGC-01-ebessos.kmz \
	 examples/858umbh1.kmz \
	 examples/2007-04-22-FLY-5094-01.kmz
.PRECIOUS: $(EXAMPLES:%.kmz=%.olc)

examples: $(EXAMPLES)

examples/2007-04-22-FLY-5094-01.kmz: examples/2007-04-22-FLY-5094-01.igc examples/2007-04-22-FLY-5094-01.gpx examples/leonardo.kml
	$(IGC2KMZ) -z 2 -o $@ -r examples/leonardo.kml \
		-i $< \
		-u http://www.paraglidingforum.com/modules.php\?name=leonardo\&op=show_flight\&flightID=6807 \
		-x examples/2007-04-22-FLY-5094-01.gpx \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_7963.jpg \
			-d "Climbing at Pormenaz and looking back at the Brevant (2525m) and the Mont Blanc (4810m)" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_7961.jpg \
			-d "Looking right at the Pointe d'Anterne (2733m)" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_7966.jpg \
			-d "Approaching the Passage de Derochoir (2246m) at 42km/h " \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_7967.jpg \
			-d "Nice cloud above the Pointe de Plate (2554m)" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_7968.jpg \
			-d "Look right at the Desert de Plate" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_7977.jpg \
			-d "On the transition from Varan to the Aravis" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_7981.jpg \
			-d "Looking right at the A 40 autoroute from Geneva" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_7982.jpg \
			-d "Looking left at Sallanches " \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_7986.jpg \
			-d "Climbing to the north of the Quatre Tetes (2364m)" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_7995.jpg \
			-d "Joining Damien climbing past the Pointe Percee (2750m)" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_7998.jpg \
			-d "Looking back past the Quatre Tetes to Varan" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8000.jpg \
			-d "Following Damien towards the Col des Aravis (where he started his flight)" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8004.jpg \
			-d "Lots of snow and a long way to the first cloud, but people like Damien succeeded to come from the Col, so it has to be possible to get back!" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8005.jpg \
			-d "Looking right across the Aravis to the Bargy" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8010.jpg \
			-d "Looking back at the Pointe Percee - I'm already below ridge height" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8009.jpg \
			-d "Passing the col between the Tardevant and La Mia - Tom got through with 3m to spare!" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8012.jpg \
			-d "The cloud over the Tete Pelouse (2539m) is now within reach" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8013.jpg \
			-d "Damien found a climb even before the Tete Pelouse and we all gratefully climbed up above the ridge after him. The Croisse Baulet (2220m) is in the background. " \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8017.jpg \
			-d "Back above the ridge looking down on the Roche Pertia above the Lac de Confins" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8018.jpg \
			-d "Looking back over the Pare de Joux (2384m) towards Mont Lachat de Chatillon (2050m) which is a popular paraglider takeoff in the summer" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8020.jpg \
			-d "Looking back at the Pointe Percee - I'm happy how easy it turned out to be despite the snow" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8019.jpg \
			-d "Looking ahead past the Tete Pelouse to the Col des Aravis" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8021.jpg \
			-d "The La Clusaz ski area is still running!" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8023.jpg \
			-d "Having crossed the col the next target is the Tournette (2351m) which has a perfect cloud waiting for us!" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8025.jpg \
			-d "Climbing above the Orsiere and looking back at the Chaine des Aravis" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8031.jpg \
			-d "Following Tom on the easy transition from Sulens to Tournette" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8029.jpg \
			-d "A picture of perfection!" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8038.jpg \
			-d "At cloudbase at 3000m above Tournette (2351m) " \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8042.jpg \
			-d "The next target is the Roc des Boeufs across Lac d'Annecy - but is it working over there yet\?" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8045.jpg \
			-d "Looking right at the Dents de Lanfon (1824m) (left) and the Dents de Cruet (1833m) (right)" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8048.jpg \
			-d "Looking south past the end of the lake into the heart of the Bauges" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8051.jpg \
			-d "The first cloud appears above the south end of the Rocs des Boeufs - so it is working, at least at the south end!" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8057.jpg \
			-d "Arriving above the Rocs des Boeufs and looking south east towards Faverge " \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8055.jpg \
			-d "Looking back at the Tournette (2351m)" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8061.jpg \
			-d "After an easy (lucky) run down the Rocs des Boeufs (1774m) I climb out and look back north at the lake" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8060.jpg \
			-d "My plan is to go round the Dent d'Arclusaz (2040m) (far right) before heading east back to Chamonix - but first I must fly over Trelod (2181m) " \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8069.jpg \
			-d "Passing over the village of Ecole on my way from Trelod to the Dent d'Arclusaz - the fields are yellow with dandelions I guess!" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8068.jpg \
			-d "How perfect is that cloud\? I think it looks a bit like a rabbit (with a minature elephant on it's back)" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8072.jpg \
			-d "Leaving the cloud after a powerful 5 m/s climb above the Dent d'Arclusaz - starting on the way home to Chamonix" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8082.jpg \
			-d "Passing Albertville - I can see Mont Blanc (and therefore home) in the distance " \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8085.jpg \
			-d "The long transition from the Pointe de la Sambuy to the end of the Aravis - running parallel with the Dents de Cons (2062m)" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8087.jpg \
			-d "Passing Faverge on my left" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8088.jpg \
			-d "Passing over Marlens before connecting with the end of the Aravis - the valley wind makes it possible to get up from very low" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8096.jpg \
			-d "Thirty minutes of hard work later and I'm finally climbing near Mont Charvin (2409m) - I notice the cloud at the far end of the Aravis is getting very dark" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8099.jpg \
			-d "After Tom and I finish climbing above Charvin we decide to divert to avoid the development to the north east" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8101.jpg \
			-d "This is anyway the direct route home - there is quite a big cloud over Megeve but so far it looks okay" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8107.jpg \
			-d "No photos for 40 minutes because of the concentration I needed to find a climb and also because we got rained on by the cloud!" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8103.jpg \
			-d "Safely above Mont Joly (2525m) and we know that we're home safe - yeah!!!" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8110.jpg \
			-d "Climbing out from Mont Joly (2525m)" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8109.jpg \
			-d "Following Lucas home to the Chamonix Valley" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8108.jpg \
			-d "Cloudbase is above the Col de Miage (3367m) - was a tour of Mont Blanc possible today? There is probably still too much snow" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8120.jpg \
			-d "Passing under the amazing Glacier de la Griaz under the Aiguille du Gouter (3863m) " \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8123.jpg \
			-d "Flying to join Tom climbing above a spur" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8125.jpg \
			-d "Looking up at the Aiguille du Midi I notice that the cloudbase is higher than it - might it be possible to climb up there?" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8131.jpg \
			-d "Still far below the Mont Blanc (4810m) but I'm now above 3800m!" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8132.jpg \
			-d "The target is in sight! The Aiguille du Midi (3842m) (left), the Refuge des Cosmiques (3613m) (middle) and the Mont Blanc du Tacul (4248m) (right)" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8130.jpg \
			-d "The Mont Blanc du Tacul (4248m)" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8129.jpg \
			-d "My dream for ages has been to fly over the Aiguille du Midi cable car station" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8157.jpg \
			-d "The Refuge des Cosmiques (3613m)" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8158.jpg \
			-d "Fly past of the refuge" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8145.jpg \
			-d "Wow!" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8147.jpg \
			-d "The last lift has gone down so the place is deserted" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8151.jpg \
			-d "The incredible cable car station of the Aiguille du Midi" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8162.jpg \
			-d "Passing the Aiguille du Midi paraglider take off ridge with the Grand Jorasses (4208m) in the distance" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8165.jpg \
			-d "Looking back I see that cloudbase is already coming down below the Aiguille du Midi - I can't believe my luck to have got there just at the right moment!" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8167.jpg \
			-d "Passing the Aiguille des Grandes Charmoz (3444m) and looking though to the Grand Jorasses (4208m)" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8170.jpg \
			-d "Looking over at the Mer de Glace at the Aiguille Verte (4102m) with its nose in the clouds" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8182.jpg \
			-d "Nearly down in Chamonix - the work is finally finished on the new town square - it's really nice!" \
		-p http://qking.web.cern.ch/qking/2007/p_chamonix/images/img_8180.jpg \
			-d "After seven and half hours and 155km I finally prepare to land back at the landing field near the Plan Praz telecabine - what an amazing day!"

examples/2008-06-07-FLY-6113-01.kmz: examples/2008-06-07-FLY-6113-01.igc examples/2008-06-07-FLY-6113-01.gpx examples/pgcomps.org.uk.kml
	$(IGC2KMZ) -z 2 -o $@ -r examples/pgcomps.org.uk.kml \
		-t examples/2008-06-07-FLY-6113-01.gpx \
		-i examples/2008-06-07-FLY-6113-01.igc

examples/2008-06-07-FLY-6113-01.gpx: examples/2008-06-07-FLY-6113-01.igc
	$(IGC2TASK) -o $@ $< \
		-n "British Open Pedro Bernardo Task 5" \
		--tz-offset 2 \
		--start-radius 21000 \
		--start-time 14:45 \
		--ess-radius 1000

examples/2008-06-16-xgd-001-01.kmz: examples/2008-06-16-xgd-001-01.igc examples/2008-06-16-xgd-001-01.gpx examples/ukxcl.kml
	$(IGC2KMZ) -z 2 -o $@ -r examples/ukxcl.kml \
		-i $< \
		-g "Axis Mercury" \
		-u http://www.pgcomps.org.uk/xcleague/xc/viewFlight.php\?xcFlightId=4139 \
		-x examples/2008-06-16-xgd-001-01.gpx

examples/2008-07-28-XPG-KVE-02.kmz: examples/2008-07-28-XPG-KVE-02.igc examples/2008-07-28-XPG-KVE-02.gpx examples/xcontest.kml
	$(IGC2KMZ) -z 2 -o $@ -r examples/xcontest.kml \
		-i $< \
		-u http://www.xcontest.org/2008/world/en/flights/detail:charlie/28.7.2008/09:23 \
		-x examples/2008-07-28-XPG-KVE-02.gpx

examples/2008-09-05-CGP-XAGC-01-ebessos.kmz: examples/2008-09-05-CGP-XAGC-01-ebessos.igc examples/2008-09-05-CGP-XAGC-01-ebessos.gpx
	$(IGC2KMZ) -z 3 -o $@ \
		-i $< \
		-t examples/2008-09-05-CGP-XAGC-01-ebessos.gpx

examples/2008-09-05-CGP-XAGC-01-ebessos.gpx: examples/2008-09-05-CGP-XAGC-01-ebessos.igc
	$(IGC2TASK) examples/2008-09-05-CGP-XAGC-01-ebessos.igc \
		-o $@ \
		--tz-offset 3 \
		--start-time 14:30 \
		--start-radius 1000

examples/858umbh1.kmz: examples/858umbh1.igc examples/858umbh1.gpx examples/xcontest.kml
	$(IGC2KMZ) -z 2 -o $@ -r examples/xcontest.kml \
		-i $< \
		-n "Martin Bühler" \
		-g "UP Edge" \
		-u http://www.xcontest.org/2008/world/en/flights/detail:umbh/8.5.2008/08:21 \
		-x examples/858umbh1.gpx

examples/leonardo.kml: $(BRAND2KML)
	$(BRAND2KML) \
		-o $@ \
		-n Leonardo \
		-u http://www.paraglidingforum.com/modules.php\?name=leonardo\&op=list_flights \
		-i http://www.paraglidingforum.com/modules/leonardo/templates/basic/tpl/leonardo_logo.gif

examples/xcontest.kml: $(BRAND2KML)
	$(BRAND2KML) \
		-o $@ \
		-n XContest \
		-u http://www.xcontest.org/ \
		-i http://www.xcontest.org/img/xcontest.gif

examples/pgcomps.org.uk.kml: $(BRAND2KML)
	$(BRAND2KML) \
		-o $@ \
		-n "British Paragliding Competitions" \
		-u http://www.pgcomps.org.uk/ \
		-i http://www.pgcomps.org.uk/ssl/aerofoil_shadow_348.gif

examples/ukxcl.kml: $(BRAND2KML)
	$(BRAND2KML) \
		-o $@ \
		-n "UK XC League" \
		-u http://www.pgcomps.org.uk/ \
		-i http://www.pgcomps.org.uk/images/bhpaH.jpg

%.gpx: %.olc
	bin/olc2gpx.py $< > $@

%.olc: %.igc $(OLC2002)
	$(OLC2002) $< > $@
