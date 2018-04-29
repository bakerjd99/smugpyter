`SmugPyter` NOTES
=================

Remarks about outstanding tasks and other `SmugPyter` issues.
Base 36 GUIDS cross reference *the history* of `TODO.md`.

### April 29, 2018

* `PATCH` requests are missing in action again. The command to change keywords
   that worked last week has stopped working. I'm sure there are perfectly
   logical reasons but I am still annoyed. The return code provides no hint
   but it's clear from looking at the web site the command is not working.
   I have seen this many times over the last ten years. What was working
   stops working - sometimes for good reasons but mostly because eccentric 
   users like myself are such a tiny portion of SmugMug's business that they
   can make these changes without stampeding *enough* paying customers.
   Regardless I will change `SmugPyter` so I can easily set the damn keywords
   by hand if necessary.
   
### March 19, 2018

 * Over the weekend I applied *kmeans* to all the images
   I have on [SmugMug](https://conceptcontrol.smugmug.com).  
   The results are mixed. Many of the generated
   color keys are perfectably reasonable and many are questionable.
   The dominant color many not be a "photographically significant color."  
   Assigning color keys that better align with photographer expectations
   will require deeper image analysis. I may try some common image segmentation
   techniques and also see if guiding *kmeans* with common photo composition
   rules like the *rule of thirds* will help. However, this will have to wait for other
   projects. I'll live with the keys for now.

### March 16, 2017

 * `<_573ot7sb11hcqdizl282wcnke_>` I've added a 
   [notebook](https://github.com/bakerjd99/smugpyter/blob/master/notebooks/Finding%20Dominant%20Color%20Names%20from%20Color%20Space%20Coordinates%20and%20Images.ipynb) 
   about using *kmeans* to compute "nearest" named colors.  I abandoned a 
   brightness suffix when I realized that named web colors 
   span a sufficient range of light and dark tones.

### March 10, 2017

 * `<_e7uijzo51rni98iqyknhnu9av_>` I have made enough progress testing
   *kmeans* based dominant color calculations to realize that what *kmeans*
   picks as a dominant color and what photographers consider an
   interesting or key color are two different things.  By assigning
   multiple colors keys to an image you an mitigate a bad single choice
   but this increases the keyword count and clutters image displays. I
   will use one color key. It may be "questionable" for one image 
   but spread over thousands of images the color keys will offer
   another useful way of partitioning pictures.   

### March 8, 2017

 * `<_e7uijzo51rni98iqyknhnu9av_>` Introduce a class to compute dominant image color and brightness, e.g. keywords
   like, `blue_light`, `blue_dark`, `blue_medium`, `violet_dark`, `gray_dark`, `gray_medium`
   
   The methods I have looked at for computing dominant colors using *kmeans* are not entirely stable. 
   Repeated runs may produce a slightly different but plausible color key. This may be OK for
   my purposes. I only want to form ad hoc groups of images that are roughly related by color.
   
   I will start by using web color names. [Web colors define 147 standard color names.](http://www.colors.commutercreative.com/grid/)
   I am not certain if that will be enough. I may still have to append brightness suffixes.

   I have decided to change the syntax of color keys to distinguish them from other keywords.
   For example the color `gold` may match the metal `gold`. I don't want the metal eliminated 
   if the color key changes to a `goldish` hue.  Hence, color keys will look like:
   `0_darksalmon`, `0_mediumpurple`, `0_navajowhite`.  The `0_` prefix differs from 
   standard keywords that do not start with numerals and print size keys that look like
   `5x5`, `4x6`.  The prefix also has the nice property of moving to the front
   of alphabetically sorted keywords.