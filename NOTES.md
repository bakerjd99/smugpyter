`SmugPyter` NOTES
=================

Remarks about outstanding tasks and other `SmugPyter` issues.
Base 36 GUIDS cross reference *the history* of `TODO.md`.

### March 8, 2017

 * `<_e7uijzo51rni98iqyknhnu9av_>` Introduce a class to compute dominant image color and brightness, e.g. keywords
   like, `blue_light`, `blue_dark`, `blue_medium`, `violet_dark`, `gray_dark`, `gray_medium`
   
   The methods I have looked at for computing dominant colors using *kmeans* are not entirely stable. 
   Repeated runs may produce a slightly different but plausible color key. This may be ok for
   my purposes. I only want to form adhoc groups of images that are roughly related by color.
   
   I will start by using web color names. [Web colors define 147 standard color names.](http://www.colors.commutercreative.com/grid/)
   I am not certain if that will be enough. I may still have to append brightness suffixes.

   I have decided to change the syntax of color keys to distinquish them from other keywords.
   For example the color `gold` may match the metal `gold`. I don't want the metal eliminated 
   if the color key changes to a `goldish` hue.  Hence, color keys will look like:
   `0_darksalmon`, `0_mediumpurple`, `0_navajowhite`.  The `0_` prefix differs from 
   standard keywords that do not start with numerals and print size keys that look like
   `5x5`, `4x6`.  The prefix also has the nice property of moving to the front
   of alphabetically sorted keywords.