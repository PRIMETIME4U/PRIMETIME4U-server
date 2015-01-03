## PRIMETIME4U

The only app that allows you to plop down to the couch and simply enjoy a movie.

[PRIMETIME4U Site](http://hale-kite-786.appspot.com/)

[PRIMETIME4U Client](https://github.com/PRIMETIME4U/PRIMETIME4U-client)

Google Technologies for Cloud and Web Development - Rome 2014/2015

## Free API
We provide also to you for free a simple API in order to get Italian TV schedules. You could ask the schedule of today, tomorrow and the day after tomorrow of the free TV, SKY TV and Mediaset Premium TV.

1. Go to:

   ```
   http://hale-kite-786.appspot.com/schedule/<type>/<day>
   ```
   >Where ```<type>``` is one of this:
   >   * **FREE** for the FREE TV;
   >   * **SKY** for the SKY TV;
   >   * **PREMIUM** for the Mediaset Premium TV;
   
   >and ```<day>``` instead one of this:
   >   * **TODAY** for the schedule of today;
   >   * **TOMORROW** for the schedule of tomorrow;
   >   * **FUTURE** for the schedule of the day after tomorrow;
      
2. The JSON returned is similar to this:

   ```json
   {
     "code": 0, 
     "data": {
       "day": "today", 
       "type": "free",
       "schedule": [
         {
           "channel": "Rai 3", 
           "originalTitle": "The Blues Brothers", 
           "time": "21:10", 
           "title": "The Blues Brothers - I fratelli Blues"
         },
         {
           "channel": "Italia 1", 
           "originalTitle": "Dead Poets Society", 
           "time": "21:30", 
           "title": "L'attimo fuggente"
         }
       ]
     }
   }   
   ```
   
3. Enjoy!

## Author
Claudio Pastorini, Dorel Coman, Giovanni Colonna, Marius Ionita