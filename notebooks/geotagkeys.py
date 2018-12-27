# -*- coding: utf-8 -*-
import csv
import requests
import smugpyter


class GeotagKeys(smugpyter.SmugPyter):

    def __init__(self, *, verbose=False, yammer=False, log_start=False):
        """ class constructor """
        super().__init__(log_start=log_start, yammer=yammer, verbose=verbose)

    def geotag_images(self, manifest_file, *, split_delimiter=';', geotag_key='geotagged'):
        """
        Sets a geotagged keyword for nongeotagged images with nonzero latitude or longitude.
        """
        image_count, change_count = 0, 0
        with open(manifest_file, 'r') as f:
            reader = csv.DictReader(f, dialect='excel', delimiter='\t')
            for row in reader:
                if self.bad_geotag_keys(row):
                    raise ValueError(
                        "(ImageKey, Latitude, Longitude, Keywords) missing in -> " + manifest_file)
                image_count += 1
                key = row['ImageKey']
                latitude = float(row['Latitude'])
                longitude = float(row['Longitude'])
                if latitude != 0.0 or longitude != 0.0:
                    keywords = row['Keywords']
                    inkeys = [s.strip().lower()
                              for s in keywords.split(split_delimiter)]

                    # if an image is already geotagged skip it
                    if geotag_key in inkeys:
                        continue

                    outkeys = list(set(inkeys))
                    outkeys.append(geotag_key)
                    outkeys = sorted(outkeys)
                    new_keywords = (split_delimiter+' ').join(outkeys)
                    outkeys = self.standard_keywords(
                        new_keywords, split_delimiter=split_delimiter)
                    same, new_keywords = (set(outkeys) == set(
                        inkeys), (split_delimiter+' ').join(outkeys))
                    if not same:
                        change_count += 1
                        self.change_image_keywords(key, new_keywords, row)
        return (image_count, change_count)

    def set_all_geotags(self, root):
        """
        Scan all manifest files in local directories and set
        geotags for images with nonzero latitude or longitude
        that are not geotagged.

            gk = GeotagKeys()
            gk.set_all_geotags(r'c:\SmugMirror\Mirror')
        """
        return self.scan_do_local_files(root, func_do=self.geotag_images)

    def reverse_geocode(self, latitude, longitude):
        """
        Returns state or province and country keywords from latitude and longitude.
        """
        count_reverse_codes = (0, [])
        latlng = '%s,%s' % (latitude, longitude)
        reverse_geocode_url = self.reverse_geocode_url + "%s&key=%s"
        reverse_geocode_url = reverse_geocode_url % (
            latlng, self.google_maps_key)
        results = requests.get(reverse_geocode_url)
        results = results.json()

        if results["status"] == "OK":
            try:
                state_country = results["results"][-2]['formatted_address']
                reverse_keys = self.standard_keywords(
                    state_country, split_delimiter=',')
                count_reverse_codes = (len(reverse_keys), reverse_keys)
            except Exception as e:
                # ignore any errors - no reverse geocodes for you
                count_reverse_codes = (0, [])
                print('unable to reverse geocode %s' % latlng)

        return count_reverse_codes

    def reverse_geocode_images(self, manifest_file, *, split_delimiter=';', geotag_key='geotagged'):
        """
        Reverse geocode images with nonzero latitude and longitude.
        """
        changed_keywords = []
        image_count, change_count = 0, 0
        with open(manifest_file, 'r') as f:
            reader = csv.DictReader(f, dialect='excel', delimiter='\t')
            for row in reader:
                if self.bad_geotag_keys(row):
                    raise ValueError(
                        "(ImageKey, Latitude, Longitude, Keywords) missing in -> " + manifest_file)
                image_count += 1
                key = row['ImageKey']
                latitude = float(row['Latitude'])
                longitude = float(row['Longitude'])
                if latitude != 0.0 or longitude != 0.0:
                    keywords = row['Keywords']
                    inkeys = [s.strip().lower()
                              for s in keywords.split(split_delimiter)]

                    # if an image is already geotagged skip it - edit the
                    # changes file and strip (geotag_key) to reprocess
                    if geotag_key in inkeys:
                        continue

                    reverse_count, reverse_keywords = self.reverse_geocode(
                        latitude, longitude)
                    if reverse_count == 0:
                        continue
                    else:
                        outkeys = inkeys + reverse_keywords
                        outkeys.append(geotag_key)
                        outkeys = sorted(list(set(outkeys)))
                        new_keywords = (split_delimiter+' ').join(outkeys)
                        outkeys = self.standard_keywords(
                            new_keywords, split_delimiter=split_delimiter)
                        same, new_keywords = (set(outkeys) == set(
                            inkeys), (split_delimiter+' ').join(outkeys))
                        if not same:
                            change_count += 1
                            if self.verbose == True:
                                print(row['FileName'] + ' | ' + new_keywords)
                            key_change = {'ImageKey': key, 'AlbumKey': row['AlbumKey'],
                                             'FileName': row['FileName'], 'Keywords': new_keywords}
                            changed_keywords.append(key_change)
                            self.all_keyword_changes[key] = key_change
                            
        # when no images are changed return a header place holder row
        if change_count == 0:
            changed_keywords.append({'ImageKey': None, 'AlbumKey': None, 'FileName': None,
                                     'Keywords': None})
            
        return (image_count, change_count, changed_keywords)
    
    def write_geotag_keyword_changes(self, manifest_file):
        """
        Write TAB delimited file of changed geotag keywords.
        Return album and keyword (image_count, change_count) tuple.

            manifest_file = r'c:\SmugMirror\Places\Overseas\Ghana1970s\manifest-Ghana1970s-Kng6tg-w.txt'
            write_geotag_keyword_changes(manifest_file)  
        """
        return self.write_keyword_changes(manifest_file, func_keywords=self.reverse_geocode_images)
    
    def update_all_geotag_keyword_changes(self, root):
        """
        Scan all manifest files in local directories and
        generate TAB delimited CSV print size keyword changes files.

            gk = GeotagKeys()
            gk.update_all_geotag_keyword_changes(pk.local_directory)
        """
        print("processing geotag keys")
        self.all_keyword_changes = {}
        imc = self.scan_do_local_files(root, func_do=self.write_geotag_keyword_changes)
        self.write_all_keyword_changes(self.all_geotag_changes_file)
        return imc
    
    def set_all_reverse_geocodes(self, root):
        """
        Scan all manifest files in local directories and set
        reverse geocode keys for nongeotagged images with nonzero
        latitude or longitude.

            gk = GeotagKeys()
            gk.set_all_reverse_geocodes(r'c:\SmugMirror\Mirror')
        """
        return self.scan_do_local_files(root, func_do=self.reverse_geocode_images)

    @staticmethod
    def bad_geotag_keys(row):
        bad = row["ImageKey"] is None or row["ImageKey"] == ""
        bad = bad or row["Latitude"] is None or row["Latitude"] == ""
        bad = bad or row["Longitude"] is None or row["Longitude"] == ""
        bad = bad or row["Keywords"] is None or row["Keywords"] == ""
        return bad


# if __name__ == '__main__':
#   gk = GeotagKeys()
#   gk.set_all_reverse_geocodes('c:\SmugMirror')
