## PRIMETIME4U

![](https://github.com/PRIMETIME4U/PRIMETIME4U-baseclient/blob/master/app/src/main/res/drawable-xhdpi/ic_launcher.png)

*The only app that allows you to plop down to the couch and simply enjoy a movie.*

## What is it?
PRIMETIME4U is an app that simply help you in the daily choose of your movie for your evening. It collects your tastes and it finds for you the best movie in the evening. It's Android based, so we suggest you to read more detailed informations in client repository:

[PRIMETIME4U Client](https://github.com/PRIMETIME4U/PRIMETIME4U-baseclient)



Google Technologies for Cloud and Web Development - Rome 2014/2015

## Free API
We also provide you for free a simple API in order to get Italian TV movie schedules. You can ask the schedule of today, tomorrow and the day after tomorrow of the FREE TV, SKY TV and Mediaset Premium TV.

1. Go to:

   ```
   http://hale-kite-786.appspot.com/api/schedule/<type>/<day>
   ```
   Where ```<type>``` is one of this:
      * **FREE** for the FREE TV;
      * **SKY** for the SKY TV;
      * **PREMIUM** for the Mediaset Premium TV;
   
   and ```<day>``` is one of this:
      * **TODAY** for the schedule of today;
      * **TOMORROW** for the schedule of tomorrow;
      * **FUTURE** for the schedule of the day after tomorrow;
      
2. An example of the JSON returned:

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

## Milestones Presentations
* [Presentation](https://docs.google.com/presentation/d/19qKrPd4RucjXbaYAIZSWszlza7LIScu43dSb3Ocs0Ho/edit?usp=sharing)
* [First Milestone - Proof of Concept](https://docs.google.com/presentation/d/1H3YqDTtFXiGIQH8ecC3wZh0_IsNmkk-EFlov9rLRiZs/edit?usp=sharing)
* [Second Milestone - Release Candidate](https://docs.google.com/presentation/d/1kWeeZnHb7-r61PwAKrXXs_ju91rtxJQp4NqhB4pkPWM/edit?usp=sharing)
* [Third Milestone - Final](https://docs.google.com/presentation/d/1pG_mtee2JS781fDr59QpuWwJXesfn4GTx23WXP1SNig/edit?usp=sharing)

## Author
Claudio Pastorini, Dorel Coman, Giovanni Colonna, Marius Ionita
