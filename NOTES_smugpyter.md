`SmugPyter` NOTES
=================

Remarks about outstanding tasks and other `SmugPyter` issues.
Base 36 GUIDS cross reference *the history* of `TODO_smugpyter.md`.

### January 31, 2022

* I have been using `SmugPyter` for a number of years now. It's
  been reliably collecting the metadata I care about without giving
  me too much grief but I am now in the process of moving the program
  to a new Windows PC and I'm being forced into making some changes.
  `SmugPyter` ran under Python 3.6 the new machine is at 3.9. It seems
  there have been some changes to libraries and so forth that typically
  break old scripts. I'd rather not get into this but as I'm the sole creator and user of this program I have no choice. 
  
### October 16, 2019

* I've added about a dozen new print sizes to `smug_default_sizes`.
  I use other print vendors like Walmart on occasion and they support
  sizes you don't find on SmugMug. Also, many of my older
  images have sizes like `3x5`, `5x6`, `6x10` and lately `9x16`.
  All these ratios come from the Picture Window Pro 
  cropping tool. Finally, many of my panoramas are
  nonstandard making them a nuisance to print. Specialty
  printers like `artmill.com` support panorama ratios 
  like `8x32` and `6x30` so I've added enough sizes
  to support proportions up to `6:1`.

* I had to increase the aspect ratio rounding precision to
  distinguish ratios after these additions.

* Finally, `PATCH` remains broken. It's only a problem
  for me when making mass changes. Otherwise the work 
  around described below meets my needs.

### December 27, 2018

* I've reorganized the keyword calculations so they
  can all be updated in one run. Prior to this change
  I had to set geotag keywords on SmugMug and collect
  the changes before computing size and color keys.
  Now I only need to:

  1.  Refresh recent metadata.
  2.  Update sample images.
  3.  Update keywords.

  All keyword changes are collected in `AllChanges.txt` 
  when I figure out why `PATCH` is broken only the contents
  of this file needs to be posted. In the meanwhile   `AllChanges.txt`
  is handy for manual updates.

### December 20, 2018

 * I've spent more time than I should have experimenting with
   variations on how I am computing color keys in `colorkeys.py`.
   I've opted to go with a revised algorithm that grades colors
   by a metric that rolls frequency, distance and *chromicity*
   into a single value defined thus:

   $$m = f_i^2 + (1 - d_i)^2 + c_i^2$$

   Keys with high $m$ values will be frequent, close and "colorful."
   
   This algorithm results in more evenly distributed colors than
   prior methods. It draws from the same `webcolors` list of named
   colors and uses the same color key syntax.

   See this this notebook for details.
   
   [
Finding Dominant Color Names from Color Space Coordinates and Images
](https://github.com/bakerjd99/smugpyter/blob/master/notebooks/Finding%20Dominant%20Color%20Names%20from%20Color%20Space%20Coordinates%20and%20Images.ipynb)

### November 30, 2018

* While implementing my nonrecursive gallery scan I noticed
  that some local paths were not coming out as expected. The
  problem had nothing to do with my code. The SmugMug API
  picks up custom folder names when building `ParentFolders`
  one of my folders had an embedded delimiter character that
  confused my parent folder parsing. I will have to check
  these settings for all my folders. 

### November 28, 2018

* I have been using `SmugPyter` for a few months now - long
  enough to observe the good and the bad. 
  
  Starting with the bad: the other day while tracking down a bug
  in a related program that consolidates all the metadata collected
  by `SmugPyter` into an SQLite database. I noticed that `SmugPyter`
  was not visiting all galleries. The recursive tree walk omitted at
  least two galleries. This is an embarrassing blunder. I should have
  detected this months ago. I have mocked up a nonrecursive
  gallery scan that will be more reliable and easier to debug.
  Also, `PATCH` requests come and go - mostly they go. 

  As for the good, day to day use of `SmugPyter` is proving less
  onerous than expected. I update images in small batches.
  Keeping the keys set for small batches is easy even with 
  the broken `PATCH`.

  A few small additions would make `SmugPyter` easier to use.
  I plan on adding some functions to compute all the keys
  of single images when given an image key or file name.
  I've noticed a number of key assignment errors while editing keys.
  Going back to original keys would be handy when such errors are discovered.
  
  Also, it may be useful to experiment with only scanning galleries
  that have been recently updated.  If the `SmugMug` update timestamps are
  reliable they could be used to avoid scanning galleries that haven't changed. 
   
### June 10, 2018

* I've made numerous changes to `SmugPyter` to support erratic
  `PATCH` requests. Patch commands are still not working and I
  haven't pursued the issue with SmugMug. The program now writes
  an `AllChanges.txt` in the root of the local directories that
  captures all keyword `PATCH` requests. It's easy to set the
  keywords manually using this file by simply cutting and pasting.
  This will do for the small number of images I typically upload
  from day to day. *It will not do for massive keyword changes!*

  I have also run [autopep8](https://pypi.org/project/autopep8/) over
  `SmugPyter` code. My experience with code pretty printers is fairly typical.
  If you start applying a particular pretty printer to new code 
  you will quickly adjust to its idiosyncracies. If you attempt to
  mass reformat large amounts of old code you will usually wreak
  things. `SmugPyter` is new enough to tolerate pretty printing and
  it does make it easier for others.

### May 2, 2018

*  A lovely little message from the Google API folks today informed me that
   they would soon be requiring a credit card for all "keyed" API use. I was
   reassured that my limited reverse geocoding of at most a dozen locations
   per month would probably qualify for their under $200 per month plan and remain
   free. You can imagine my relief.  Even in my use remains free I don't like
   the idea of handing a credit card number over to Google so I started looking
   around for free reverse geocoding sites and immediately found an alternative
   that is not only free for small time uses but easier to use as well.
   
   [https://nominatim.openstreetmap.org/reverse?format=json&lat=43.58955&lon=-116.22855&zoom=18&addressdetails=1](https://nominatim.openstreetmap.org/reverse?format=json&lat=43.58955&lon=-116.22855&zoom=18&addressdetails=1)
   
   I will adjust `SmugPyter` to use this service.
   

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