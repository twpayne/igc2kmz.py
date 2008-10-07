#include <stdio.h>
#include <stdlib.h>
   extern double atof();
#include <string.h>  /* strlen() */
#include <math.h>
#include <malloc.h>
#include <signal.h>
#ifndef FALSE
#define FALSE 0
#endif
#ifndef TRUE
#define TRUE !FALSE
#endif
#ifndef STDIN
#define STDIN 0
#endif
#ifndef EOS
#define EOS '\0'
#endif
#define MAXPOINTS 5000
#define RELEASE "$Revision: 1.3 $ $Date: 2008/06/04 14:12:40 $"

/*
 *	Liste der eingelesenen Längen- und Breitengarde
 */
   typedef int t_daytime; /* at least 60*60*24=86400 seconds */
   typedef int t_index;   /* point counter */

   static t_index pnts=0;  /* no of points in track */
   static double    *latpnts=0;
   static double    *lonpnts=0;
   static t_daytime *timepnts=0; /* und der Tageszeit in Sekunden */
   typedef struct _point {
      double lat, lon;
      struct _point *next;
      t_daytime seconds;
   } t_point;
   static t_point *pointlist = 0;

/*
 *	Distanzmatrix von jedem Punkt i zu jedem Punkt j i<=j
 * Die Berechnung erfolgt mit doubles, das Ergbnis wird auf ganze Meter gerundet
 * ganzzahig gespeichert, um später schneller damit rechnen zu können
 * Vorsicht: Rechnerabhängiger Ganzzahlenbereich muß 25mal so groß sein,
 * wie die maximale Länge einer Strecke in Metern!
 * Wegen Symmetrie ist nur das obere rechte Dreieck gefüllt, für
 * dmval[i][j] mit i>j verwendet man einfach dmval[j][i]
 */
   typedef int t_distance; /* meters */
/* static t_distance dmval[MAXPOINTS][MAXPOINTS]; */
   static t_distance *distance = 0;
   static t_distance maxdist = 0; /* maximale Distanz in Metern zwischen zwei beliebigen Punkten, des Tracks */
   static t_distance max2dist = 0; /* maximale Distanz in Metern zwischen zwei aufeinanderfolgenden Punkten */

/*
 *	eingelesenen Punkt in Liste der Längen- und Breitengrade aufnehmen
 */
    static void addPoint(double lat, double lon, int seconds) {
      static t_point *last = 0;
      t_point *neu;
   /*	if (pnts>=MAXPOINTS) {
   	fprintf(stderr,"more than %d points are not allowed\n", pnts);
   	exit(-1);
   }
   timepnts[pnts]=seconds; latpnts[pnts]=lat;  lonpnts[pnts++]=lon; */
      if (!(neu=(t_point*)malloc(sizeof(t_point)))) { perror("optigc: not enough memory"); exit(1); }
      neu->lat = lat; neu->lon = lon; neu->seconds = seconds; neu->next = 0;
      if (!pointlist) {
         pointlist = neu;
      } 
      else {
         last->next = neu;
      }
      last = neu;
      pnts++;
   }

/*
 *	Distanzberechnung für Testzewecke und ggf. initiale Überprüfung des Tracks
 */
    static double calcdistance(double lat1, double lon1, double lat2, double lon2) {/* in metern */
      static double pi_div_180 = ((double)M_PI)/((double)180.0);
      static double d_fak = ((double)6371000.0); /* FAI Erdradius in Metern */
   /* Radius nautischen Meilen: ((double)1852.0)*((double)60.0)*((double)180.0)/((double)M_PI); */
      static double d2    = ((double)2.0);
      double sinlon, sinlat, latx, laty, lonx, lony;
      latx = lat1 * pi_div_180; lonx = lon1 * pi_div_180;
      laty = lat2 * pi_div_180; lony = lon2 * pi_div_180;
      sinlat = sin((latx-laty)/d2);
      sinlon = sin((lonx-lony)/d2);
      return d2*asin(sqrt( sinlat*sinlat + sinlon*sinlon*cos(latx)*cos(laty)))*d_fak;
   }

/*
 *	für Testzwecke: Vergleich Distanzen in Distanzmatrix mit direkter Berechnung
 */ /*
static void comparedistances(int p1, int p2) {
	printf("dist(%d,%d)=%d meter ?= %lf\n",p1,p2,dmval[p1][p2],
		distance(latpnts[p1],lonpnts[p1],latpnts[p2],lonpnts[p2])
	);
} */


/*
 *	Ausgabe von Grad in Grad:Minuten.huntertstel Minuten, wie im OLC-Formular
 */
    static void printdegrees(double latlon) {
      int degrees = (int)latlon;
      double minutes = (latlon - (double)(degrees))*((double)60.0);
      printf("%2d:%02.3lf",degrees, minutes);
   }

/*
 *	Ausgabe des i-ten Trackpunktes in Koordinatenform mit Angabe
 * von nord/süd für Breiten, bzw. ost/west für Längen
 */
    static void printpoint(int i) {
      double lat, lon;
      int signlat, signlon, hours, minutes, seconds;
      lat = latpnts[i]; lon = lonpnts[i];
      if (lat<0) {
         lat *= (double)(-1.0); 
         signlat = -1;
      } 
      else {
         signlat = 1;
      }
      if (lon<0) {
         lon *= (double)(-1.0); 
         signlon = -1;
      } 
      else {
         signlon = 1;
      }
      hours = (minutes = (seconds = timepnts[i])/60)/60;
      seconds -= 60*minutes;
      minutes -= 60*hours;
      printf("p%04d %02d:%02d:%02d %c", i+1, hours, minutes, seconds, (signlat<0)?'S':'N');
      printdegrees(lat);
      printf(" %c", (signlon<0)?'E':'W');
      printdegrees(lon);
   }


/*
 *	Alle Distanzen zwischen allen Punkten berechnen und in Distanzmatrix speichern
 * Die Berechnung erfolgt mit doubles, das Ergbnis wird auf ganze Meter gerundet
 * ganzzahig gespeichert, um später schneller damit rechnen zu können
 * Vorsicht: Rechnerabhängiger Ganzzahlenbereich muß 25mal so groß sein,
 * wie die maximale Länge einer Strecke in Metern!
 */
    static void initdmval() {
      static double pi_div_180 = ((double)M_PI)/((double)180.0); /* Umrechnung Grad ins Bogenmaß */
      static double d_fak = ((double)6371000.0); /* FAI-Erdradius in metern */
      double *sinlat; /* Für schnellere Berechnung sin/cos-Werte merken */
      double *coslat;
      double *lonrad;
      t_point *old;
      double latrad, sli, cli, lri;
      register int i, j, dist, cmp;
      long  duration;
      int maxp1,maxp2,max2p1,max2p2;
      int max_t1,max_t2;
      t_distance max_t_dist;
   	
      if (latpnts) free(latpnts);
      if (lonpnts) free(lonpnts);
      if (timepnts) free(timepnts);
      if (!(timepnts=(t_daytime*)malloc(sizeof(t_daytime)*pnts))) { perror("optigc mem: "); exit(1); }
      if (!(lonpnts=(double*)malloc(sizeof(double)*pnts))) { perror("optigc mem: "); exit(1); }
      if (!(latpnts=(double*)malloc(sizeof(double)*pnts))) { perror("optigc mem: "); exit(1); }
      if (!(distance=(t_distance*)malloc(sizeof(t_distance)*pnts*pnts))) { perror("optigc mem: "); exit(1); }
      if (!(sinlat=(double*)malloc(sizeof(double)*pnts))) { perror("optigc mem: "); exit(1); }
      if (!(coslat=(double*)malloc(sizeof(double)*pnts))) { perror("optigc mem: "); exit(1); }
      if (!(lonrad=(double*)malloc(sizeof(double)*pnts))) { perror("optigc mem: "); exit(1); }
      printf("DEBUG initializing cos/sin/rad..\n");
      cmp = pnts+1; /* für indexberechnung i,i */
      for(i=0;i<pnts;i++) { /* alle Punkte ins Bogenmaß umrechnen und sin/cos Speichern */
         lonrad[i] = (lonpnts[i] = pointlist->lon) * pi_div_180;
         sinlat[i] = sin( (latrad = (latpnts[i]=pointlist->lat) * pi_div_180) );
         coslat[i] = cos(latrad);
         timepnts[i] = pointlist->seconds;
         pointlist = (old=pointlist)->next;
         free(old);
         distance[cmp*i] = 0; /* Diagonale der Matrix mit Distanz 0 füllen */
      }
      printf("DEBUG initializing distances..\n");

      maxdist = 0; /* maximale Distanz zwischen zwei beliebigen Punkten neu berechnen */
      max2dist = 0; /* maximale Distanz zwischen zwei aufeinanderfolgenden Punkten neu berechnen */
      max_t_dist=0; /* max takeoff distance */

      cmp = pnts-1; /* Schleifenvergleichswert für schnelle Berechnung vorher merken */

      maxp1=maxp2=max2p1=max2p2=0;

      max_t1=max_t2=0;
      max_t_dist=0;

      for(i=0;i<cmp;i++) { /* diese Schleife NICHT RÜCKWÄRTS!!! */

         sli = sinlat[i]; 
	 cli = coslat[i]; 
	 lri = lonrad[i];

         j = i+1;

         if ( (distance[i+pnts*j] = 
		dist = 
		(int)(d_fak*acos(sli*sinlat[j] + cli*coslat[j]* cos(lri-lonrad[j]))+((double)0.5))  /* auf meter runden */
         	) > max2dist) {

		max2p1=i;
		max2p2=j;
		max2dist = dist; /* weiteste Distanz merken */
	 }

	 /* compute max distnace from point 0 (takeoff */
         if ( ((int)distance[pnts*j])  > max_t_dist) {
		max_t2=i;
		max_t_dist = (int)distance[pnts*j]; 
	 }


         for(j=i+2;j<pnts;j++) { /* Durchlauf j=i+1 rausgezogen */
            if ( (distance[i+pnts*j] = dist = (int)(d_fak*acos(
            					sli*sinlat[j] + cli*coslat[j]* cos(lri-lonrad[j])
            									)+((double)0.5))  /* auf meter runden */
            	) > maxdist) {

		maxp1=i;
		maxp2=j;

		maxdist = dist; /* ggf. weiteste Distanz merken */
	  }

         /* DEBUG if (i+1==j) { comparedistances(i,j); } */
         }
      }
      free(lonrad); free(coslat); free(sinlat);
      if (max2dist > maxdist) {
	maxdist = max2dist;
	maxp1=max2p1;
	maxp2=max2p2;
      }

      printf("DEBUG maximal distance between any 2 points: %d meters\n", maxdist);
      printf("OUT MAX_LINEAR_DISTANCE %d\n", maxdist);
      printf("DEBUG P1: %d\n", maxp1);
      printf("DEBUG P2: %d\n", maxp2);


	 printf("OUT TYPE FreeFlight0TP\n");
         printf("OUT FLIGHT_KM %.3lf\n",(float)maxdist/1000 );
         printf("OUT FLIGHT_POINTS %.3lf\n",(float)maxdist/1000 );
         printf ("OUT "); printpoint(maxp1); printf("\n");
         printf ("OUT "); printpoint(maxp2); printf(" %3.3lf km\n",
            ((double)distance[maxp1+pnts*maxp2])/((double)1000.0) );


	 printf("OUT TYPE MaxTakeoffDistance\n");
         printf("OUT FLIGHT_KM %.3lf\n",(float)max_t_dist/1000 );
         printf("OUT FLIGHT_POINTS %.3lf\n",(float)max_t_dist/1000 );
         printf ("OUT "); printpoint(max_t1); printf("\n");
         printf ("OUT "); printpoint(max_t2); printf(" %3.3lf km\n",
            ((double)distance[max_t1+pnts*max_t2])/((double)1000.0) );


      printf("DEBUG START_TIME %d\n", timepnts[0]);
      printf("DEBUG END_TIME %d\n", timepnts[pnts-1]);
   	duration= timepnts[pnts-1]- timepnts[0];
   	printf("DEBUG DURATION_SEC %d\n",duration);
   	printf("DEBUG DURATION %2d:%2d:%2d\n",duration/3600,(duration%3600 )/60,duration%60);
      printf("DEBUG maximal distance between 2 successive points: %d meters\n", max2dist);
   }

/*
 *	Indexe der 5 besten Punkte für: freie Strecke, FAI-Dreieck und flaches Dreieck
 */
   static int max1=0, max2=0, max3=0, max4=0, max5=0;
   static int max1fai=0, max2fai=0, max3fai=0, max4fai=0, max5fai=0;
   static int max1flach=0, max2flach=0, max3flach=0, max4flach=0, max5flach=0;
   static int maxroute = 0, bestfai=0, bestflach=0;

/*
 *	laufende Indexe während der Berechnung, für die asynchrone Ausgabe von
 * Zwischenergebnissen, z.B. in der Signalbehandlungsroutine
 */
   static int i1, i2, i3, i4, i5;


/*
 *	Beste Lösungen für Freie Strecke, flaches Dreieck und FAI-Dreieck
 * mit Gesamtstrecke in km und Punktzahl auf 1000stel genau ausgeben
 * beim OLC werden Punkte auf 100stel gerundet, über das Runden von
 * Teilstrecken ist keine Aussage gemacht, der OLC-Server scheint
 * aber bereits Teilstrecken auf 100stel km = dezimeter zu runden.
 * Trotzdem wird hier in Metern und nicht in Dezimetern gerechnet,
 * da es sonst zu Rundungsfehlern kommt.
 
 * Best Score for free distance, flat triangle and FAI triangle 
 * spend exactly with total distance in km and score on 1000stel 
 * with the OLC points are rounded on 100stel, more?ber rounding 
 * No statement is made stages, which seems OLC server to however already round 
 * stages on 100stel km = dezimeter. 
 * Nevertheless in meters and not in dezimetern one counts here, 
 * comes there it otherwise to rounding errors.
 */
 
    static void printbest() {
   
      double freeFlightKm  =((double)maxroute)/(double)1000.0;
      double freeTriangleKm=((double)bestflach)/(double)1000.0;
      double FAITriangleKm =((double)bestfai)/(double)1000.0;
   
      double freeFlightPoints   = freeFlightKm   *((double)1.5);
      double freeTrianglePoints = freeTriangleKm *((double)1.75);
      double FAITrianglePoints  = FAITriangleKm  *((double)2.0);
   
   
      if ( freeFlightPoints > freeTrianglePoints && freeFlightPoints > FAITrianglePoints ) {
         printf("OUT BEST_FLIGHT_TYPE FREE_FLIGHT\n");
      } else if ( freeTrianglePoints > FAITrianglePoints ) {      
	      /*
	      *	Die Dreiecke bestehen aus den Schenkeln a, b und c. Von dieser Strecke
	      * wird die Distanz d zwischen Start- und Endpunkt abgezogen
	      */
	         printf("OUT BEST_FLIGHT_TYPE FREE_TRIANGLE\n");
	   } else {
          printf("OUT BEST_FLIGHT_TYPE FAI_TRIANGLE\n");
       }

		/* Print all opti results          */
		
         printf("OUT TYPE FREE_FLIGHT\n");
         printf("OUT FLIGHT_KM %.3lf\n",freeFlightKm );
         printf("OUT FLIGHT_POINTS %.3lf\n",freeFlightPoints );
      
         printf("DEBUG Best free Flight: %.3lf km = %.3lf Points\n",freeFlightKm,freeFlightPoints );
         printf ("OUT "); printpoint(max1); printf("\n");
         printf ("OUT "); printpoint(max2); printf(" %3.3lf km\n",
            ((double)distance[max1+pnts*max2])/((double)1000.0) );
         printf ("OUT "); printpoint(max3); printf(" %3.3lf km\n",
            ((double)distance[max2+pnts*max3])/((double)1000.0) );
         printf ("OUT "); printpoint(max4); printf(" %3.3lf km\n",
            ((double)distance[max3+pnts*max4])/((double)1000.0) );
         printf ("OUT "); printpoint(max5); printf(" %3.3lf km\n",
            ((double)distance[max4+pnts*max5])/((double)1000.0) );
      
    
         printf("OUT TYPE FREE_TRIANGLE\n");
         printf("OUT FLIGHT_KM %.3lf\n",freeTriangleKm );
         printf("OUT FLIGHT_POINTS %.3lf\n",freeTrianglePoints );
      
         printf("DEBUG Best free Triangle: %.3lf km = %.3lf Points\n",
            ((double)bestflach)/(double)1000.0, ((double)bestflach)/((double)1000.0)*((double)1.75) );
         printf ("OUT "); printpoint(max1flach); printf("\n");
         printf ("OUT "); printpoint(max2flach); printf(" %3.3lf km=d\n",
            ((double)distance[max1flach+pnts*max5flach])/(double)1000.0);
         printf ("OUT "); printpoint(max3flach); printf(" %3.3lf km=a\n",
            ((double)distance[max2flach+pnts*max3flach])/(double)1000.0);
         printf ("OUT "); printpoint(max4flach); printf(" %3.3lf km=b\n",
            ((double)distance[max3flach+pnts*max4flach])/(double)1000.0);
         printf ("OUT "); printpoint(max5flach); printf(" %3.3lf km=c\n",
            ((double)distance[max2flach+pnts*max4flach])/(double)1000.0);


         printf("OUT TYPE FAI_TRIANGLE\n");
         printf("OUT FLIGHT_KM %.3lf\n",FAITriangleKm );
         printf("OUT FLIGHT_POINTS %.3lf\n",FAITrianglePoints );
      
         printf("bestes FAI Dreieck: %.3lf km = %.3lf Punkte\n",
            ((double)bestfai)/(double)1000.0, ((double)bestfai)/((double)1000.0)*((double)2.0) );
         printf ("OUT "); printpoint(max1fai); printf("\n");
         printf ("OUT "); printpoint(max2fai); printf(" %3.3lf km=d\n",
            ((double)distance[max1fai+pnts*max5fai])/(double)1000.0);
         printf ("OUT "); printpoint(max3fai); printf(" %3.3lf km=a\n",
            ((double)distance[max2fai+pnts*max3fai])/(double)1000.0);
         printf ("OUT "); printpoint(max4fai); printf(" %3.3lf km=b\n",
            ((double)distance[max3fai+pnts*max4fai])/(double)1000.0);
         printf ("OUT "); printpoint(max5fai); printf(" %3.3lf km=c\n",
            ((double)distance[max2fai+pnts*max4fai])/(double)1000.0);
      
      
      
   }

/*
 *	Signalbehandlungsroutine die bisher bester Zwischenergebnise asynchron ausgibt
 */
    static void opthandler(int signum) {
      printf("\ncurrent ");
      printbest();
      printf("current count: %d %d %d %d %d\n",i1,i2,i3,i4,i5);
      if (-1==(int)signal(signum,opthandler)) perror("signal()");
   }

/*
 * Matrix mit den kleinsten Abständen zwischen Start- und Endpunkt
 * für gegebenen ersten und dritten Wendepunkt.
 * Beispiel: dmin[5][10] ist die kleinstmögliche Distanz d zwischen 
 * Start- und Endpunkt, wenn Punkt 5 der erste und Punkt 10 der 3te
 * Wendepunkt ist. dmini[5][10] leifert dann, den Index des zugehörigen
 * Startpunktes und dminj[5][10] den Index des Endpunktes für diese
 * minimale Distanz
 * Dies Matritzen werden mit quadratischem Aufwand vorab berechnet,
 * da sie zur Bestimmung von Dreiecken bei der Optimierung in der
 * innersten Schleife für die 3 Wendepunkte n^3 mal immer wieder
 * benötigt werden. Dadurch kann der Gesamtrechaufwand in der Größenordnung
 * von n^5 auf Größenordnung n^3+n^2 gesenkt werden.
 *
 * Hinweis: diese Matritzen sind nur im oberen rechten Dreieck besetzt:
 */
/*
static int  dmin[MAXPOINTS][MAXPOINTS];   hierfür wird unbesetzte Ecke von distance genutzt
static int dmini[MAXPOINTS][MAXPOINTS];
static int dminj[MAXPOINTS][MAXPOINTS];   diese beiden teilen sich die folgende Matrix */
   static t_index *dminindex = 0;
#define dmini(x,y) dminindex[(x)+pnts*(y)]
#define dminj(x,y) dminindex[(y)+pnts*(x)]

/*
 *	für Debuggingzwecke können die Matrizen ausgegeben werden
 */ /*
static void printdmin() {
	int i, j;
	for(i=0;i<pnts;i++) {
		printf("i=%d ",i);
		for(j=0; j<pnts;j++) {
			printf("d:%di:%dj:%d ",dmin[i][j],dmini[i][j],dminj[i][j]);
		}
		printf("\n");
	}
} */

/*
 * berechne kleinste Distanz dmin(i,j) zwischen allen Punkten x und y mit x<=i und y>=j
 *   für alle x<=i, y>=j: dmin(i,j) <= dmin(x,y)
 *      und dmval[dmini[i][j]][dminj[i][j]] <= dmval[x][y]
 */
#define dmin(x,y) distance[(y)+pnts*(x)]
/* untere linke Ecke von distance für dmin nutzen */
    static void initdmin() {
      register int i, j, d, mini, minj, minimum = maxdist;
   
      printf("initializing dmin(i,j) with best start/endpoints for triangles..\n");
      if (!(dminindex=(t_index*)malloc(sizeof(t_index)*pnts*pnts))) { perror("mem"); exit(1); }
      for(j=pnts-1;j>0;j--) { /* erste Zeile separat behandeln */
         d = distance[0+pnts*j];
         if (d<minimum) {/* d<=minimum falls gleichwertiger Punkt weiter vorne im track gefunden werden soll */
            minimum = d; minj = j;
         }
         dmin(0,j)  = minimum;
         dmini(0,j) = 0;
         dminj(0,j) = minj;
      }
      for(i=1;i<pnts-1;i++) { /* folgenden Zeilen von vorheriger ableiten */
         j=pnts-1; /* letzte Spalte zur Initialisierung des Minimums getrennt behandeln */
         minimum = dmin(i-1,j); mini = dmini(i-1,j); minj = dminj(i-1,j);
         d = distance[i+pnts*j];
         if (d<minimum) {
            minimum = d; mini = i; minj = j;
         }
         dmin(i,j)  = minimum;
         dmini(i,j) = mini;
         dminj(i,j) = minj;
         for(j=pnts-2;j>i;j--) { /* andere spalten von hinten nach vorne bearbeiten */
            d = distance[i+pnts*j];
            if (d<minimum) { /* aktueller Punkt besser als bisheriges Minimum? */
               /* d<=minimum falls gleichwertiger Punkt weiter vorne im track gefunden werden soll */
               minimum = d; mini = i; minj = j;
            }
            if ((d=dmin(i-1,j))<minimum) { /* Minimum aus vorheriger Zeile besser? */
               minimum = d; mini = dmini(i-1,j); minj = dminj(i-1,j);
            }
            dmin(i,j)  = minimum;
            dmini(i,j) = mini;
            dminj(i,j) = minj;
         }
      }
   /* printdmin(); */
   }

#define fdmin(x,y) dmin(x,y)
/*
int fdmin(int i, int j) {
	if ((i<0)||(i>=pnts)) printf("out of bound error: i=%d\n", i);
	if ((j<0)||(j>=pnts)) printf("out of bound error: j=%d\n", j);
	return dmin[i][j];
}
*/
#define fdmini(x,y) dmini(x,y)
#define fdminj(x,y) dminj(x,y)

   static t_distance *maxenddist = 0;
   static t_index *maxendpunkt=0;

/*
 *	berechnet den besten Endpunkt für Freie Strecke bei gegebenem 3ten Wendepunkt
 */
    void initmaxend() {
      register int w3, i, f, maxf, besti, leaveout;
      printf("initializing maxenddist[] with maximal distance to best endpoint ..\n");
      if (!(maxenddist=(t_distance*)malloc(sizeof(t_distance)*pnts))) { perror("mem"); exit(1); }
      if (!(maxendpunkt=(t_index*)malloc(sizeof(t_index)*pnts))) { perror("mem"); exit(1); }
      for(w3=pnts-1; w3>1; w3--) {
         maxf = 0; leaveout = 1;
         for(i=besti=pnts-1; i>=w3; i -= leaveout) {
            if ((f = distance[w3+pnts*i]) >= maxf) {
               maxf = f; besti = i;
            }
            if ((leaveout = (maxf - f)/max2dist)<1) leaveout = 1;
         }
         maxenddist[w3]  = maxf;
         maxendpunkt[w3] = besti;
      }
   }
#define maxend(v) maxenddist[(v)]
#define maxendi(v) maxendpunkt[(v)]
/*
int maxend(int w3) {}
int maxendi(int w3) {}
*/

/*
 * berechnet eine initiale geratene Lösung, damit leaveouts von Anfang an groß sind
 */
    void firstguess() {
      int a, b, c, d, u, tmp;
   /* geratene Lösung für freie Strecke: */
   /* max1 = 0;       /* Start ganz vorne */
   /* max2 = pnts/4;  /* Erste Wende nach einem 4tel der Strecke */
   /* max3 = pnts/2;  /* Zweite Wende etwa in der Mitte */
   /* max4 = pnts*3/4;/* Dritte Wende etwa nach 3/4teln der Strecke */
   /* max5 = pnts-1;  /* Endpunkt ganz hinten */
   
      max1 = pnts*3/8;       /* Start ganz vorne */
      max2 = pnts*4/8;  /* Erste Wende nach einem 4tel der Strecke */
      max3 = pnts*5/8;  /* Zweite Wende etwa in der Mitte */
      max4 = pnts*6/8;/* Dritte Wende etwa nach 3/4teln der Strecke */
      max5 = pnts-1;  /* Endpunkt ganz hinten */
      maxroute = distance[max1+pnts*max2] + distance[max2+pnts*max3] + distance[max3+pnts*max4] + distance[max4+pnts*max5];
   
   /* geratene Lösung für ein Dreieck begonnen auf einem Schenkel */
      i1 = 0;       /* Start ganz vorne */
      i2 = pnts/6;  /* Erste Wende nach einem Sechstel */
      i3 = pnts/2;  /* Zweite Wende in der Mitte */
      i4 = pnts*5/6;/* Dritte Wende */
      i5 = pnts-1;  /* Endpunkt ganz hinten */
      a = distance[i2+pnts*i3];
      b = distance[i3+pnts*i4];
      c = distance[i2+pnts*i4];
      d = distance[i1+pnts*i5];
      u = a + b + c;
      if (d*5 <= u) { /* zufällig ein Dreieck gefunden? */
         tmp = u * 7;
         if ((a*25>=tmp)&&(b*25>=tmp)&&(c*25>=tmp)) { /* zufällig FAI-D gefunden? */
            bestfai = u - d;
            max1fai = i1; max2fai = i2; max3fai = i3; max4fai = i4; max5fai = i5;
         } 
         else { /* Flaches Dreieck */
            bestflach = u - d;
            max1flach = i1; max2flach = i2; max3flach = i3; max4flach = i4; max5flach = i5;
         }
      }
   
   /* geratene Lösung für eine Dreieck begonnen an erster Wende */
      i1 = i2 = 0;     /* Start und erste Wende ganz vorne */
      i3 = pnts/3;     /* zweite Wende nach 1/3 der Strecke */
      i4 = pnts*2/3;   /* dritte Wende nach 2/3 der Strecke */
      i5 = pnts-1;     /* Endpunkt ganz hinten */
      a = distance[i2+pnts*i3];
      b = distance[i3+pnts*i4];
      c = distance[i2+pnts*i4];
      d = distance[i1+pnts*i5];
      u = a + b + c;
      if (d*5 <= u) { /* zufällig ein Dreieck gefunden? */
         tmp = u * 7;
         if ((a*25>=tmp)&&(b*25>=tmp)&&(c*25>=tmp)) { /* zufällig FAI-D gefunden? */
            if ((u-d)>bestfai) {
               bestfai = u - d;
               max1fai = i1; max2fai = i2; max3fai = i3; max4fai = i4; max5fai = i5;
            }
         } 
         else { /* Flaches Dreieck */
            if ((u-d)>bestflach) {
               bestflach = u - d;
               max1flach = i1; max2flach = i2; max3flach = i3; max4flach = i4; max5flach = i5;
            }
         }
      }
   }

#define MIN(x,y) (x<y)?x:y
#define MAX(x,y) (x>y)?x:y

/*
 *	führt die Eigentliche Optimierung (über 3 Punkte) durch
 * mrme   = maxroute - e
 * mrmemf = maxroute - e -f
 * bflpdmc ) bestflach +d -c
 */
    static void optimize(int nocalc) {
      register int i4cmp, i1leaveout, fsleaveout, flachleaveout, leaveout, faileaveout, dreieckleaveout, i2cmp = pnts-2, max2d2, max2d7, max2d3;
      register int i, a, b, c, d, e, f, u, w, tmp, maxaplusb, aplusb, c25, d5minusc, mrmemf, mrme, bflpdmc, dmc, baipdmc, epf;
      if (pnts<5) {
         printf("only %d points given, no optimization\n",pnts);
         return;
      }
      initdmval();
      if (nocalc) return;

      initdmin();
      initmaxend();
      max1 = max2 = max3 = max4 = max5 = maxroute= bestfai = bestflach = 0;
      max2d2 = max2dist * 2; max2d7 = max2dist * 7; max2d3 = max2dist * 3;
      firstguess();
      printf("calculating best waypoints.. for more than 500 points need some minutes, press Ctrl-C for intermediate results..\n");
      signal(SIGINT, opthandler);
      for(i2=0; i2<i2cmp; i2++) { /* 1.Wende */ /* i1leaveout = 1; kann wech */
         for(i=i1=e=0; i<i2; i+=i1leaveout) { /* Starting point for free distance is separately optimized  */
            if ((tmp = distance[i+pnts*i2])>=e) { e = tmp; i1 = i; }
            i1leaveout = 1;
         	/*  MANOLIS if ((i1leaveout=(e-tmp)/max2dist)<1) i1leaveout = 1; */
         } /* e, i1 enthalten fuer dieses i2 den besten Wert  e, i1 contain the best value for this i2  */
         mrme = maxroute - e; i4cmp = i2+2;
         for(i4=pnts-1; i4>=i4cmp; i4-=leaveout) { /* 3.Wende von hinten optimieren */
            c25 = (c = distance[i2+pnts*i4])*25; d5minusc = (d = fdmin(i2,i4))*5-c;
            bflpdmc = bestflach + (dmc =d - c); baipdmc = bestfai + dmc;
            maxaplusb = 0; /* leaveout = 1;  eigentlich nicht notwendig */
            f = maxend(i4); mrmemf = mrme -f;  epf = e + f;
            for(i=i3=i2+1; i<i4; i+=leaveout) { /* 2.Wende separat optimieren */
               if ((aplusb=(a=distance[i2+pnts*i])+(b=distance[i+pnts*i4]))>maxaplusb) { /* findet größtes a+b (und auch größtes Dreieck) */
                  maxaplusb = aplusb; i3 = i;
               }
               if (d5minusc<=aplusb) { /* Dreieck gefunden 5*d<= a+b+c */
                  if ((c25>=(tmp=(u=aplusb+c)*7))&&(a*25>=tmp)&&(b*25>=tmp)) { /* FAI-D gefunden */
                     if ((w=u-d)>bestfai) { /* besseres FAI-D gefunden */
                        max1fai = fdmini(i2,i4);
                        max2fai = i2; max3fai = i; max4fai = i4;
                        max5fai = fdminj(i2,i4);
                        baipdmc = (bestfai = w) + dmc;
                     }
                  } 
                  else { /* nicht FAI=flaches Dreieck gefunden */
                     if ((w=u-d)>bestflach) {
                        max1flach = fdmini(i2,i4);
                        max2flach = i2; max3flach = i; max4flach = i4;
                        max5flach = fdminj(i2,i4);
                        bflpdmc = (bestflach = w) + dmc;
                     }
                  }
               }
            /* leaveout = 1; */
               fsleaveout = (mrmemf - aplusb)/max2d2+1; /* +1 wg. > */
            /* if (fsleaveout>1) { */
               dreieckleaveout = (d5minusc - aplusb)/max2d2;
               flachleaveout = (bflpdmc-aplusb)/max2d2+1; /* +1 wg > */
               faileaveout = (baipdmc-aplusb)/max2d2+1; /* +1 wg > */
               leaveout = MIN(flachleaveout,faileaveout);
               leaveout = MAX(leaveout,dreieckleaveout);
               leaveout = MIN(leaveout,fsleaveout);
               if (leaveout<1) leaveout = 1;
            	/* MANOLIS */
               leaveout=1;
            /*}*/
            /* printf("leaveouts: fs=%d dr=%d fl=%d fai=%d insgesamt=%d\n", fsleaveout,dreieckleaveout,flachleaveout,faileaveout,leaveout); */
            } /* maxaplusb, i3 enthalten fuer dieses i2 und i4 besten Wert */
            if ((tmp = maxaplusb+epf) > maxroute) {
               max1 = i1; max2 = i2; max3 = i3; max4 = i4; max5 = maxendi(i4);
               mrme = (maxroute = tmp) -e;
            }
         /* leaveout = 1;*/
         /* if (( */ fsleaveout = (mrmemf - maxaplusb)/max2d2+1;  /* )>1) { */
            dreieckleaveout = (d5minusc - maxaplusb)/max2d7;
            flachleaveout = (bflpdmc - maxaplusb)/max2d3+1;
            faileaveout = (baipdmc - maxaplusb)/max2d3+1;
            leaveout = MIN(flachleaveout,faileaveout);
            leaveout = MAX(leaveout,dreieckleaveout);
            leaveout = MIN(leaveout,fsleaveout);
            if (leaveout<1) leaveout = 1;
         /* } */
         }
      }
      printbest();
      free(maxendpunkt); free(maxenddist);
      free(dminindex);
   }

/*
 *	Gradangabe aus dem String in der IGC-Datei in Gradzahl umwandeln
 */
    static double getlatlon(char *str) {
      double latlon;
      str[7] = EOS;
      latlon = atof(&(str[2]))/(double)60000.0;
      str[2] = EOS;
      latlon += atof(str);
      return latlon;
   }

    static double getlatlon2(char *str) {
      double latlon;
      str[8] = EOS;
      latlon = atof(&(str[3]))/(double)60000.0;
      str[3] = EOS;
      latlon += atof(str);
      return latlon;
   }
/*
 *	IGC-Datei einlesen, dabei Punkte in Punkteliste merken
 * Aufeinanderfolgende Punkte mit selbem Zeitstempel werden weggelassen,
 * wenn sie auch die selben Koordinaten haben
 * Aufeinanderfolgende Punkt mit den selben Koordinaten (oder sehr kleiner
 * Distanz) könnten auch ausgelassen werden.

 * IGC file read in, points in point list notice 
 * Successive points with same time stamp are omitted, 
 * if it also the same coordinates have 
 * Successive point with same coordinates (or very smaller distance) 
 * could be also omitted.
 */
    static void analyzeIGC(FILE *in, int verbose, double maxspeed, int starttime, int endtime) {
      int i = 0, hint0 = 0, hint5 = 0;
      char line[255];
      int last = 0, seconds, minutes, hours, current, deltaseconds, first = TRUE;
      double lastlat=(double)0.0, lastlon=(double)0.0, lat, lon, signlat, signlon, tmp, speed;
      
   	double maximum_speed=0,mean_speed=0;
   	unsigned int alt,last_alt,max_alt=0,min_alt=60000,takeoff_alt;
   	double dalt,min_dalt=0,max_dalt=0;
   	
      pnts = 0; pointlist = 0;
   
      printf("starttime: %d endtime: %d\n", starttime, endtime);
   
      while (fscanf(in,"%s", line)==1) {
         if ( *line != 'B') {
	    if (line[0] =='H' &&  line[1] =='F' && line[2] =='D' && line[3] =='T' && line[4] =='E') {
	        printf("DEBUG DATE %s\n",&line[5]);   /*  the date is HFDTE140702 */
            }
            continue;
	 }
       /*  if ( line[15] != '0') 
            continue; */
         if ( (line[14] != 'N') && (line[14] != 'S')) 
            continue;
         if ( (line[23] != 'E') && (line[23] != 'W')) 
            continue;
         if (strlen(line) < 23) 
            continue;
         if (line[14]=='N') signlat = (double)1.0;
         if (line[14]=='S') signlat = (double)(-1.0);
         if (line[23]=='W') signlon = (double)1.0;
         if (line[23]=='E') signlon = (double)(-1.0);
         line[14] = EOS;  line[23] = EOS;
         
         
      	line[35] = EOS;
       	alt=atoi(&line[30]);  
      	

         if (verbose) printf("%04d N%s E%s alt %dm ", i+1, &line[7], &line[15],alt);
         lat = signlat * getlatlon(&line[7]);
         lon = signlon * getlatlon2(&line[15]);
         
      
      	line[7] = EOS;
         seconds = atoi(&line[5]);
         line[5] = EOS;
         minutes = atoi(&line[3]);
         line[3] = EOS;
         hours   = atoi(&line[1]);
         current = seconds + 60*minutes + 3600*hours;
         if (current<starttime) 
            continue;
         if (current>endtime) 
            break;
         if (!last) {
            last = current;
            lastlat = lat; lastlon = lon;
         }
         tmp = calcdistance(lastlat,lastlon,lat,lon);
         deltaseconds = current-last;
         speed = (deltaseconds)?tmp*3.6/(deltaseconds):0.0; /* in km/h */
         /* update maximum speed */
         if (speed > maximum_speed && speed <maxspeed)  maximum_speed=speed;
      	mean_speed+=speed;
      	
      	if (i==0) takeoff_alt=alt;
      	if (alt>max_alt) max_alt=alt;
      	if (alt<min_alt) min_alt=alt;
      	
      	if (i>0)  {  /* compute vario  */
      		dalt=((double)alt-(double)last_alt)/(double)deltaseconds;
      		if (dalt>max_dalt) max_dalt=dalt;
      		if (dalt<min_dalt) min_dalt=dalt;
      	}
      	last_alt=alt;
      	
      	++i;
         if (verbose) printf("%02d:%02d:%02d dt=%ds ds=%lfm\t spd=%lfkm/h\n", hours, minutes, seconds, deltaseconds, tmp, speed);
         if (speed>=maxspeed) printf("WARNING: more than %lfkm/h at %02d:%02d:%02d, %lfkm/h\n", maxspeed, hours, minutes, seconds, speed);
         if (deltaseconds<0) printf("WARNING: timewrap before %02d:%02d:%02d\n", hours , minutes, seconds);
         if (current!=last) {
            if (tmp<((double)0.5)) { /* smaller distance than 0,5 meters is no measurable */
               if (last) {
                  hint5++;
               } 
               else addPoint(lat,lon,current);
            } 
            else addPoint(lat,lon,current);
         } 
         else { /* punkte mit 0 Zeitunterschied auslassen */
            if (tmp>=((double)0.5)) {
               addPoint(lat,lon,current);
               printf("WARNING: dtime=0 but dstrecke=%lf\n",tmp);
            } 
            else {
               if (!first) {
                  if (tmp!=0.0) printf("WARNING: dtime=0 dstrecke=%lf point left out!\n",tmp);
                  else hint0++;
               } 
               else { /* ersten Punkt nicht weglassen */
                  addPoint(lat,lon,current); first=FALSE;
               }
            }
         }
         last = current; lastlat = lat; lastlon = lon;
      }
      if (hint0) printf("HINT: %d points left out, due to dt=0 ds=0!\n",hint0);
      if (hint5) printf("HINT: %d points with nearly zero distance deleted\n",hint5);
      if (!verbose) printf("%d trackpoints read.\n",pnts);
      
      mean_speed=mean_speed/pnts;
      printf("DEBUG MAX_SPEED %f\n",maximum_speed);     
		printf("DEBUG MEAN_SPEED %f\n",mean_speed);
      printf("DEBUG MAX_ALT %d\n",max_alt);
      printf("DEBUG MIN_ALT %d\n",min_alt);
      printf("DEBUG TAKEOFF_ALT %d\n",takeoff_alt);
      printf("DEBUG MAX_VARIO %2.2f\n",max_dalt);
      printf("DEBUG MIN_VARIO %2.2f\n",min_dalt);
      
   }

/**
 *	konvertieren eines (auch unvollständigen) Zeitstrings in sekunden
 */
    static int a2s(char *str) {
      int hours=0, minutes=0, seconds=0, len;
      hours = atoi(str);
      if ((len = strlen(str))>3) minutes = atoi(&(str[3]));
      if (len>6) seconds = atoi(&(str[6]));
      return seconds+(minutes+(hours*60))*60;
   }

/*
 *	Abfrage der Programmoptionen.   -v(erbose) für Ausgabe aller Punkte
 *                                 -s#maxspeed
 * Wird kein Filename angegeben, wird von der
 * Standardeingabe gelesen (erlaubt ein Pipen der Daten ins Programm)
 */
    int main(int ac, char *av[]) {
      int i, verbose = FALSE;
      int nocalc=0;
      FILE *in;
      double maxspeed = 90.0;
      int starttime = 0;
      int endtime = 24*60*60;
      char *filename = 0;
      for (i=1; i<ac; i++) {
         if (av[i][0]=='-') {
            if (av[i][1]=='v') verbose = TRUE;
            else if (av[i][1]=='s') maxspeed = atof(&(av[i][2]));
            else if (av[i][1]=='b') starttime = a2s(&(av[i][2]));
	    else if (av[i][1]=='n') nocalc = 1;
            else if (av[i][1]=='e') endtime = a2s(&(av[i][2]));
            else if (av[i][1]=='h') {
               printf("usage: %s [-v] [-n] [-s] [-bhh[:mm[:ss]]] [-ehh[:mm[:ss]]] [-help] [ name ]\n",av[0]);
               printf("  -v    : enable verbose mode\n");
               printf("  -n    : do not optimize\n");
               printf("  -s    : use another parameter for MaxSpeed Detection, default is: %lfkmh\n",maxspeed);
               printf("  -bhh[:mm[:ss]] : begin time (points before are skipped)\n");
               printf("  -ehh[:mm[:ss]] : end time (points after this time are skipped\n");
               printf("  -help : this help screen\n");
               printf("   name : igc filename, otherwise reading from stdin\n");
               printf("  release: %s %s\n\n", av[0], RELEASE);
               return -1;
            }
            else printf("illegal option: %s\n", av[i]);
         } 
         else {
            if (filename) printf("only the last filename is used\n");
            filename = av[i];
         }
      }
      if (filename) {
         if (!(in=fopen(filename,"r"))) { perror(filename); exit(1); }
      } 
      else {
         fprintf(stderr,"reading from stdin..\n");
         if (!(in=fdopen(STDIN,"r"))) { perror("STDIN"); exit(1); }
      }
      analyzeIGC(in,verbose,maxspeed,starttime,endtime); /* IGC-File einlesen */
      fclose(in);
      optimize(nocalc); /* Track optimieren */
      return 0;
   }
