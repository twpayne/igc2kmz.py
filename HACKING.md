Photo placement
---------------

File: `igc2kmz/__init__.py`
Function: `Flight.make_photos_folder`

igc2kmz uses the EXIF information embedded in the photo to place at the location it was taken. If the EXIF information includes a GPS position then this is used, otherwise the tracklog is examined to find the pilot's location when the photo was taken.

This of course assumes that the user has set the time and date on his camera correctly, which unfortunately many people do not do. Also, if they do set it, they tend to set it to local time at home, which can be quite different from local time at the time and place of the flight and is not UTC. Unfortunately the EXIF information does not record any timezone, so we don't have complete information and the photos can end up placed incorrectly.


Thermal and glide analysis
--------------------------

File: `igc2kmz/track.py`
Function: `Track.analyse`

To identify thermals and glides a simple but effective heuristic is used. The average climb rate over 20 seconds is compared with the pilot's progress. Progress is defined as the distance travelled along the track divided by the change in position over the same period. For example, when flying in a straight line the progress is close to one, but if the pilot circles then progress drops to close to zero: the pilot travels a long distance along the track without covering much distance over the ground. Experimental investigation suggests that progress values over 0.9 correspond to gliding behaviour, and values less than this correspond to thermalling or emergency descent behaviour, even in strong winds.

Therefore we can classify the track using the following:

* progress > 0.9 ⇒ gliding
* progress < 0.9 and climb rate > 0 ⇒ thermalling
* progress < 0.9 and climb rate < 0 ⇒ emergency descent

Further refinements include ensuring that the identified features are of interest to the pilot, that is that glides are long enough, a significant amount of height is gained in a thermal, and so on.


Average, maximum and peak climb rates and thermal efficiency
------------------------------------------------------------

File: `igc2kmz/__init__.py`
Function: `Flight.make_analysis_folder`

The average climb rate is the calculated for the entire thermal, that is the total height gained divided by the time taken. Maximum climb rate is the maximum climb rate on a 20 second average. Peak climb rate is the highest climb rate observed between sequential points in the track log.

The thermal efficiency is the average climb rate divided by the maximum climb rate. A thermal efficiency of 100% corresponds to flying straight into the strongest core and staying in it until exiting the thermal. Lower values correspond to spending less time in the core or losing the thermal completely at times. This simple model assumes that the maximum climb rate is achievable from the start of the thermal to its end which is rarely the case, usually the thermal strength varies with height depending on the airmass.

In practice, thermal efficiencies over 80% are rare, 70% or higher is very good, and anything below 50% indicates broken thermals and/or poor thermalling technique.


Salient altitude analysis
-------------------------

File: `igc2kmz/util.py`
Function: `salient`

The pilot is often interested in his maximum or minimum altitude at various points. However, highlighting every local minima and maxima leads to an overwhelming number of points. The salient algorithm uses a divide and conquer technique to find all pairs of consecutive maxima and minima where the difference between them is greater than a certain threshold. Broadly speaking it proceeds as follows:

* for a given sequence x[i]..x[j], if the overall trend is upwards (i.e. x[i] < x[j]) then find the largest drop in the sequence, that is find (m, n) that maximises x[m] - x[n] subject to m < n
* if the overall trend is downwards (i.e. x[i] > x[j]) then the largest climb in the sequence, i.e find (m, n) that minimises x[m] - x[n] subject to m < n
* if the overall trend is flat (i.e. x[i] == x[j]) then compute candidate values of (m, n) using both the above and chose the value of (m, n) that maximises | x[m] - x[n] | (i.e. find both the largest drop and the largest climb and choose which ever is bigger)
* if the magnitude of this change is less than our threshold then we are done
* otherwise add m and n to the set of salient points and recurse with the sub-sequences i..m, m..n, and n..j

In the worst case the algorithm is O(N^2), but in the normal case is O(N log N). An obvious speed-up is to pre-filter the sequence to remove all monotonic sub-sequences but this has not proved necessary with the length of sequences used in the program.


Spherical geometric functions
-----------------------------

File: `igc2kmz/coord.py`
Function: `Coord.initial_bearing_to`, `Coord.distance_to`, `Coord.halfway_to`, `Coord.interpolate`, `Coord.coord_at`

All these geometric formulae are taken from this excellent page of [spherical geometry formulae](http://www.movable-type.co.uk/scripts/latlong.html). Note that all distance calculations assume that the Earth is a perfect sphere with the FAI radius (r=6371km).
