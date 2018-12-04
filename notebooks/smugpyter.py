# smugpyter.py
#
# This class uses the SmugMug API 2.0 to collect and archive
# SmugMug image metadata. The metadata is downloaded to local
# directories that mirror the structure of online SmugMug
# folders and albums. Image metadata is stored in
# durable version control friendly TAB delimted CSV files.
#
# Thumbnail and small versions of online images are also
# downloaded and stored in appropriate directories. Large sizes
# are not downloaded as all originals are stored in offline
# "secure undisclosed locations."
#
# Much of the code in this class derives from:
# https://github.com/speedenator/smuploader/blob/master/bin/smregister
# https://github.com/kevinlester/smugmug_download/blob/master/downloader.py
# https://github.com/AndrewsOR/MugMatch/blob/master/mugMatch.py
#
# modified for python 3.6/jupyter environment - modifications assisted by 2to3 tool

from rauth.service import OAuth1Service
import requests_oauthlib
from string import ascii_letters, digits
import requests
import http.client
import time
import sys
import os
import json
import configparser
import re
import shutil
import csv

# required to access mirror.db
import sqlite3

# handle iso date time string formats
from datetime import datetime, timedelta
import dateutil.parser
import pytz


class SmugPyter(object):

    smugmug_api_base_url = 'https://api.smugmug.com/api/v2'
    smugmug_upload_uri = 'http://upload.smugmug.com/'
    smugmug_base_uri = 'http://api.smugmug.com'
    smugmug_request_token_uri = 'http://api.smugmug.com/services/oauth/1.0a/getRequestToken'
    smugmug_access_token_uri = 'http://api.smugmug.com/services/oauth/1.0a/getAccessToken'
    smugmug_authorize_uri = 'http://api.smugmug.com/services/oauth/1.0a/authorize'
    smugmug_api_version = 'v2'

    reverse_geocode_url = 'https://maps.googleapis.com/maps/api/geocode/json?latlng='

    auth = None
    merge_changes = False

    # cannot create SmugPyter objects if this file is missing
    smugmug_config = os.path.join(os.path.expanduser("~"), '.smugpyter.cfg')

    def __init__(self, verbose=False, yammer=True):
        """
        Constructor. 
        Loads the config file and initialises the smugmug service
        """
        self.verbose = verbose
        self.argument_default = 'images'
        self.local_directory = 'c:/SmugMirror/'
        self.yammer = yammer
        self.all_keyword_changes = {}

        config_parser = configparser.RawConfigParser()
        config_parser.read(SmugPyter.smugmug_config)
        try:
            self.username = config_parser.get('SMUGMUG', 'username')
            self.consumer_key = config_parser.get('SMUGMUG', 'consumer_key')
            self.consumer_secret = config_parser.get(
                'SMUGMUG', 'consumer_secret')
            self.access_token = config_parser.get('SMUGMUG', 'access_token')
            self.access_token_secret = config_parser.get(
                'SMUGMUG', 'access_token_secret')
            self.local_directory = config_parser.get(
                'SMUGMUG', 'local_directory')
            self.google_maps_key = config_parser.get(
                'GOOGLEMAPS', 'google_maps_key')
            self.log_file = config_parser.get('LOGGING', 'log_file')
            self.all_keyword_changes_file = config_parser.get(
                'LOGGING', 'all_changes')
            self.mirror_database = config_parser.get('SMUGMUG', 'mirror_database')
            self.days_before = int(config_parser.get('SMUGMUG', 'days_before'))
        except:
            raise Exception(
                "Config file is missing or corrupted. Run 'python smugpyter.py'")

        self.smugmug_service = OAuth1Service(
            name='smugmug',
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            request_token_url=self.smugmug_request_token_uri,
            access_token_url=self.smugmug_access_token_uri,
            authorize_url=self.smugmug_authorize_uri)

        # NIMP: we don't need two authorizations - clean up
        self.auth = requests_oauthlib.OAuth1(self.consumer_key,
                                             self.consumer_secret, self.access_token,
                                             self.access_token_secret, self.username)

        self.request_token, self.request_token_secret = self.smugmug_service.get_request_token(
            method='GET', params={'oauth_callback': 'oob'})
        self.smugmug_session = self.smugmug_service.get_session((self.access_token,
                                                                 self.access_token_secret))
        self.append_to_log("SmugPyter started: " + time.ctime())

    def append_to_log(self, text):
        """ Append text to simple log file - creates if missing"""
        print(text)
        with open(self.log_file, "a") as log:
            log.writelines('\n' + text)

    def get_authorize_url(self):
        """
        Returns the URL for OAuth authorisation.
        """
        self.request_token, self.request_token_secret = self.smugmug_service.get_request_token(method='GET',
                                                                                               params={'oauth_callback': 'oob'})
        authorize_url = self.smugmug_service.get_authorize_url(
            self.request_token, Access='Full', Permissions='Add')
        return authorize_url

    def get_access_token(self, verifier):
        """
        Gets the access token from SmugMug.
        """
        self.access_token, self.access_token_secret = self.smugmug_service.get_access_token(method='POST',
                                                                                            request_token=self.request_token,
                                                                                            request_token_secret=self.request_token_secret,
                                                                                            params={'oauth_verifier': verifier})
        return self.access_token, self.access_token_secret

    def request_once(self, method, url, params={}, headers={}, files={}, data=None, header_auth=False):
        """
        Performs a single request.
        """
        if self.verbose == True:
            print('\nREQUEST:\nmethod='+method+'\nurl='+url +
                  '\nparams='+str(params)+'\nheaders='+str(headers))
            if len(str(data)) < 300:
                print("data="+str(data))

        response = self.smugmug_session.request(url=url,
                                                params=params,
                                                method=method,
                                                headers=headers,
                                                files=files,
                                                data=data,
                                                header_auth=header_auth)
        if self.verbose == True:
            print('RESPONSE DATA:\n' + str(response.content)[:100] + (" ... " + str(
                response.content)[-100:] if len(str(response.content)) > 200 else ""))
        try:
            data = json.loads(response.content)
        except Exception:
            pass
        return data

    def request(self, method, url, params={}, headers={}, files={}, data=None, header_auth=False, retries=5, sleep=5):
        """
        Performs requests, with multiple attempts if needed.
        """
        retry_count = retries
        while retry_count > 0:
            try:
                response = self.request_once(
                    method, url, params, headers, files, data, header_auth)
                if ('Code' in response and response['Code'] in [200, 201]) or ("stat" in response and response["stat"] in ["ok"]):
                    return response
            except (requests.ConnectionError, requests.HTTPError, requests.URLRequired,
                    requests.TooManyRedirects, requests.RequestException, http.client.IncompleteRead) as e:
                if self.verbose == True:
                    print(sys.exc_info()[0])
            if self.verbose == True:
                print('Retrying (' + str(retry_count) + ')...')
            time.sleep(sleep)
            retry_count -= 1
        print('Error: Too many retries, giving up.')
        sys.exit(1)

    def get_albums(self):
        """
        Get a list of all albums in the account.
        """
        if self.verbose == True:
            print("Getting albums")

        albums = []
        start = 1
        stepsize = 500
        while(True):
            params = {'start': start, 'count': stepsize}
            response = self.request('GET', self.smugmug_api_base_url + "/user/"+self.username+"!albums",
                                    params=params, headers={'Accept': 'application/json'})

            for album in response['Response']['Album']:
                albums.append(
                    {"Title": album['Title'], "Uri": album["Uri"], "AlbumKey": album["AlbumKey"]})

            if 'NextPage' in response['Response']['Pages']:
                start += stepsize
            else:
                break
        return albums

    def get_album_names(self):
        """
        Return list of album names.
        """
        albums = self.get_albums()
        album_names = [a["Title"] for a in albums]
        return album_names

    def get_album_id(self, album_name):
        """
        Get an album id.
        """
        if album_name == None:
            raise Exception("Album name needs to be defined")

        album_id = None
        for album in self.get_albums():
            if SmugPyter.decode(album['Title']) == SmugPyter.decode(album_name):
                album_id = album['AlbumKey']
                break
        return album_id

    def get_image_date(self, imagemeta_data):
        """
        Get an image date.

        There are a number of SmugMug image dates to choose from. The dates
        obtained from the (images) or (geomedia) options refer to upload and 
        adjustment times. The original image date must be extracted from the image
        metadata EXIF/IPTC. Sadly, the metadata tag is nonstandard and there are a 
        number of choices. This function attempts to pick the best available 
        original image date.

        """
        if 'DateTimeCreated' in imagemeta_data:
            original_date = imagemeta_data['DateTimeCreated']
            if ('' == original_date) and 'DateTimeModified' in imagemeta_data:
                original_date = imagemeta_data['DateTimeModified']
        elif 'DateTimeOriginal' in imagemeta_data:
            original_date = imagemeta_data['DateTimeOriginal']
        else:
            original_date = ''

        return original_date

    def get_album_images(self, album_id, argument='images'):
        """
        Get a list of images in an album.

        The (argument) parameter selects various API options. For
        example to select all the geotagged images in an album do:

            smug = SmugPyter()
            smug.get_album_images('gLd4hT', "geomedia")
        """
        if album_id == None:
            raise Exception("Album ID must be set to retrieve images")

        images = []
        start = 1
        stepsize = 500
        while(True):
            params = {'start': start, 'count': stepsize}
            response = self.request('GET', self.smugmug_api_base_url + "/album/"+album_id+"!" + argument,
                                    params=params, headers={'Accept': 'application/json'})

            # extract the metadata I care about
            for image in (response['Response']['AlbumImage'] if 'AlbumImage' in response['Response'] else []):
                clean_caption = self.purify_smugmug_text(image["Caption"])
                clean_keywords = self.purify_smugmug_text(image["Keywords"])
                images.append({"ImageKey": image['ImageKey'], "AlbumKey": album_id, "FileName": image["FileName"],
                               "ArchivedMD5": image["ArchivedMD5"], "ArchivedSize": image["ArchivedSize"],
                               "Latitude": image["Latitude"], "Longitude": image["Longitude"], "Altitude": image["Altitude"],
                               "OriginalHeight": image["OriginalHeight"], "OriginalWidth": image["OriginalWidth"],
                               "UploadDate": image["Date"], "LastUpdated": image["LastUpdated"], "Uri": image["Uri"],
                               "ThumbnailUrl": image["ThumbnailUrl"],
                               "Keywords": clean_keywords, "Caption": clean_caption})

            if 'NextPage' in response['Response']['Pages']:
                start += stepsize
            else:
                break

        # return images sorted by file name - this helps reduce
        # spurious line differences in TAB delimited files
        images = sorted(images, key=lambda k: k["FileName"])
        return images

    def get_album_image_names(self, album_images):
        """
        Get a list of {ImageKey, FileName} dictionaries for (album_images).

            smug = SmugPyter()
            album_images = smug.get_album_images('XghWcL')
            smug.get_album_image_names(album_images)
        """
        image_names = [{"ImageKey": i["ImageKey"],
                        "FileName": i["FileName"]} for i in album_images]
        return image_names

    def get_album_image_captions(self, album_images):
        """
        Get a list of {ImageKey, Caption} dictionaries for (album_images).
        """
        image_captions = [{"ImageKey": i["ImageKey"],
                           "Caption": i["Caption"]} for i in album_images]
        return image_captions

    def get_latitude_longitude_altitude(self, album_images):
        """
        Get a list of {ImageKey, (Latitute,Longitude,Altitude)} dictionaries for (album_images).
        """
        images_lba = [{"ImageKey": i["ImageKey"], "LatLongAlt": (i["Latitude"], i["Longitude"], i["Altitude"])}
                      for i in album_images]
        return images_lba

    def get_album_image_real_dates(self, album_images, *, realdate_dict=None):
        """
        Get a list of {ImageKey, AlbumKey, RealDate, FileName} dictionaries 
        for (album_images). 

        The performance of this function is mostly appalling
        as we must make a web request for every single image date. 
        Hence, when (realdate_dict) is not None look up real dates
        to avoid time consuming API calls. These dates are quite
        stable and seldom change.

            smug = SmugPyter(yammer=True)
            album_images = smug.get_album_images('XghWcL')
            smug.get_album_image_real_dates(album_images)
        """
        image_keys = [i["ImageKey"] for i in album_images]
        image_files = [i["FileName"] for i in album_images]
        album_keys = [i["AlbumKey"] for i in album_images]
        image_dates = []
        start = 1
        stepsize = 500
        params = {'start': start, 'count': stepsize}
        headers = {'Accept': 'application/json'}

        for key, imfile, alkey in zip(image_keys, image_files, album_keys):
            if key in realdate_dict:
                image_dict = realdate_dict[key]
                if 'RealDate' in image_dict:
                    image_date = image_dict['RealDate']
                else:
                    print('missing (RealDate) key skipping -> ' + imfile)
                    continue
            else:
                # this is ugly but I don't see any other way to get the original image EXIF dates
                self.show_yammer('getting real date -> ' + imfile)
                response = self.request('GET', self.smugmug_api_base_url + "/image/" + key + "!metadata",
                                        params=params, headers=headers)
                image_date = self.get_image_date(
                    response['Response']['ImageMetadata'])

            image_dates.append({"ImageKey": key, "AlbumKey": alkey,
                                "RealDate": image_date, "FileName": imfile})
        return image_dates

    def get_image_download_url(self, image_id):
        """
        Get the link for dowloading an image.
        """
        response = self.request('GET', self.smugmug_api_base_url + "/image/"+image_id+"!download",
                                headers={'Accept': 'application/json'})
        return response['Response']['ImageDownload']['Url']

    def create_nice_name(self, name):
        return "-".join([re.sub(r'[\W_]+', '', x) for x in name.strip().split()]).title()

    def get_album_info(self, album_id):
        """
        Get info for an album.

            smug = SmugPyter()
            smug.get_album_info('WpcrnD')
        """
        if self.verbose == True:
            print("Getting albums")

        response = self.request('GET', self.smugmug_api_base_url + "/album/"+album_id,
                                headers={'Accept': 'application/json'})
        return response["Response"]["Album"]

        # album_info = dict()
        # album_key = self.get_album_key(album_id)
        # response = self.request('GET', self.smugmug_api_uri,
        #                         params={'method': 'smugmug.albums.getInfo',
        #                                 'AlbumID': album_id, 'AlbumKey': album_key})
        # album_info['album_id'] = response['Album']['id']
        # album_info['album_name'] = response['Album']['Title']
        # album_info['category_id'] = response['Album']['Category']['id']
        # album_info['category_name'] = response['Album']['Category']['Name']
        # return album_info

    def get_child_node_uri(self, node_id):
        """
        Get child node uri.
        """
        response = self.request('GET', self.smugmug_api_base_url + "/node/" + node_id,
                                headers={'Accept': 'application/json'})
        uri = response["Response"]["Node"]["Uris"]["ChildNodes"]["Uri"]
        return uri


# NOTE: folling function does not scan all galleries - retired - will soon delete -

#    def mirror_folders_offline(self, root_uri, root_dir, func_album=None, func_folder=None):
#        """
#        Recursively walk online SmugMug folders and albums and apply
#        functions (func_album) and (func_folder).
#        """
#        root_uri = (self.smugmug_base_uri + '%s') % root_uri
#        if not '!children' in root_uri:
#            root_uri += '!children'
#        #print('url = ' + root_uri)
#        response = self.request('GET', root_uri, headers={
#                                'Accept': 'application/json'})
#        for node in response["Response"]["Node"]:
#            name = self.extract_alphanum(node["Name"])
#            path = '%s/%s' % (root_dir, name)
#            # print(path)
#            os.makedirs(path, exist_ok=True)
#            if node["Type"] == 'Folder':
#                if not func_folder == None:
#                    func_folder(name, path)
#                self.mirror_folders_offline(node["Uri"], path, func_album)
#            elif node['Type'] == 'Album':
#                print('visiting album ' + name)
#                uri = node["Uris"]["Album"]["Uri"]
#                album_id = uri.split('/')[-1]
#                if not func_album == None:
#                    func_album(album_id, name, path)

        # Queue for download
        # master_albums_list.append(path)
        #dl_queue.put({'node' : node, 'path' : path})

        # if 'NextPage' in response['Response']['Pages']:
        #    self.mirror_folders_offline(pages['NextPage'], root_dir)

    def download_album_metadata(self, days_before=0):
        
        start_time = time.clock()
        
        if days_before == 0:
            print("Collecting all albums ... ")
        else:
            print("Collecting albums changed in the last %s days" % (days_before))
            
        rinfos = self.changed_online_galleries(days_before=days_before)
        album_count = len(rinfos)
        print("Scanning %s albums" % album_count)
        for i, ainfo in enumerate(rinfos):
            print("visiting %s/%s %s ..." %
                  (i + 1, album_count, ainfo['Name']))
            parent_folders = ainfo['Uris']['ParentFolders']['Uri']
            local_path = self.local_path_from_parents(parent_folders,
                                                      self.local_directory,
                                                      self.username)
            if 0 == len(local_path):
                print("skipping empty local path -> " + ainfo['Name'])
                continue
            album_name = ((ainfo['Name']).replace(' ', '')).replace("'", '')
            local_path = local_path + album_name
            os.makedirs(local_path, exist_ok=True)
            self.write_album_metadata(
                ainfo, album_name, local_path)
            
        print("elasped seconds = %s" % (time.clock() - start_time))

#    def download_smugmug_mirror(self, func_album=None, func_folder=None):
#        """
#        Walk SmugMug folders and albums and apply functions (func_album) and (func_folder).
#
#            smug = SmugPyter()
#            smug.download_smugmug_mirror(func_album=smug.write_album_manifest)
#            smug.download_smugmug_mirror(func_album=smug.write_album_info)
#        """
#        root_folder = self.local_directory
#        folders = self.get_folders()
#        for folder in folders:
#            root_uri = self.get_child_node_uri(folder["NodeID"])
#            top_folder = self.extract_alphanum(folder["Name"])
#            self.mirror_folders_offline(root_uri, root_folder + top_folder,
#                                        func_album, func_folder)
#        print("done")

    def write_album_metadata(self, ainfo, name, path):
        """
        Write one album's TAB delimited metadata files.

        Example call:

        smug.write_album_metadata('35K9VD',
           'BanffandJasper2006',
           'C:/SmugMirror/Mirror/Trips/USAandCanada/BanffandJasper2006'
        )

        """

        # write order matters
        self.write_album_info(ainfo, name, path)
        self.write_album_manifest(ainfo['AlbumKey'], name, path)
        self.write_album_real_dates(ainfo['AlbumKey'], name, path)

    def write_album_info(self, ainfo, name, path):
        """
        Write TAB delimited file of album information.
        """
        selected_info = {'AlbumKey': ainfo['AlbumKey'],
                         'Name': ainfo['Name'],
                         'ImageCount': ainfo['ImageCount'],
                         'Date': ainfo['Date'],
                         'LastUpdated': ainfo['LastUpdated'],
                         'ImagesLastUpdated': ainfo['ImagesLastUpdated'],
                         'OriginalSizes': ainfo['OriginalSizes'],
                         'TotalSizes': ainfo['TotalSizes'],
                         'SortMethod': ainfo['SortMethod'],
                         'SortDirection': ainfo['SortDirection'],
                         'ParentFolders': self.purify_smugmug_text(ainfo['Uris']['ParentFolders']['Uri']),
                         'WebUri': self.purify_smugmug_text(ainfo['WebUri']),
                         'Description': self.purify_smugmug_text(ainfo['Description'])}
        rows = []
        rows.append(selected_info)
        mask = self.case_mask_encode(ainfo['AlbumKey'])
        ainfo_name = "ainfo-%s-%s-%s" % (name, ainfo['AlbumKey'], mask)
        ainfo_file = path + "/" + ainfo_name + '.txt'
        keys = rows[0].keys()
        with open(ainfo_file, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(
                output_file, keys, dialect='excel-tab')
            dict_writer.writeheader()
            dict_writer.writerows(rows)

    def write_album_manifest(self, album_id, name, path):
        """
        Write TAB delimited file of SmugMug image metadata.

        Example call:

        smug.write_album_manifest('9NVXV3',
           'WashingtonDC2007',
           'C:/SmugMirror/Mirror/Trips/USAandCanada/WashingtonDC2007'
        )

        """
        album_images = self.get_album_images(album_id)
        if len(album_images) == 0:
            print('empty album %s' % name)
            return None
        mask = self.case_mask_encode(album_id)
        manifest_name = "manifest-%s-%s-%s" % (name, album_id, mask)
        manifest_file = path + "/" + manifest_name + '.txt'
        keys = album_images[0].keys()
        with open(manifest_file, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(
                output_file, keys, dialect='excel-tab')
            dict_writer.writeheader()
            dict_writer.writerows(album_images)

    def write_album_real_dates(self, album_id, name, path):
        """
        Write TAB delimited file of SmugMug image real dates.

        My image dates vary from fairly reliable EXIF dates
        to wild guesses about century old prints. SmugMug 
        requires a full date and it looks in a number
        of places for full dates, see: (get_image_date).

        Example call:

        smug.write_album_real_dates('9NVXV3',
           'WashingtonDC2007',
           'C:/SmugMirror/Mirror/Trips/USAandCanada/WashingtonDC2007'
        )

        """

        # If the current folder has a real dates file look
        # up dates in this file for any images that exist in it.
        # This insures we only go to SmugMug for images
        # that do not have real image dates. To force reprocessing
        # delete images from the real dates file or
        # to reprocess all the dates in an album delete
        # the real dates file.
        mask = self.case_mask_encode(album_id)
        realdate_name = "realdate-%s-%s-%s" % (name, album_id, mask)
        realdate_file = path + "/" + realdate_name + '.txt'
        realdate_dict = {}
        if os.path.isfile(realdate_file):
            realdate_dict = self.image_dict_from_csv(realdate_file)

        album_images = self.get_album_images(album_id)
        if len(album_images) == 0:
            print('empty album %s' % name)
            return None

        real_dates = self.get_album_image_real_dates(
            album_images, realdate_dict=realdate_dict)
        if len(real_dates) == 0:
            return None

        keys = real_dates[0].keys()
        with open(realdate_file, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(
                output_file, keys, dialect='excel-tab')
            dict_writer.writeheader()
            dict_writer.writerows(real_dates)

    def get_folders(self):
        """
        Get a list of folder names under the user.
        Currently supports only top-level folders.
        """
        response = self.request('GET', self.smugmug_api_base_url + "/folder/user/"+self.username+"!folders",
                                headers={'Accept': 'application/json'})
        folders = []
        for folder in response['Response']['Folder']:
            folders.append({"Name": folder["Name"],
                            "NodeID": folder["NodeID"], "UrlName": folder["UrlName"]})
        return folders

    def get_folder_names(self):
        """
        Return list of (top-level) folder names.
        """
        folders = self.get_folders()
        folder_names = [f["Name"] for f in folders]
        return folder_names

    def get_folder_id(self, folder_name):
        """
        Get category id.
        """
        folder_id = None
        for folder in self.get_folders():
            if folder['Name'] == folder_name:
                folder_id = folder['UrlName']
                break
        return folder_id

    def larger_from_thumb_url(self, thumb_url, *, url_size='M'):
        """
        Convert a thumbnail size url to a small or medium url.
        The TAB delimited manifest files contain (ThumbnailUrl)s
        that point to online SmugMug images. It is much faster
        to convert these stored urls to larger sizes  than issue 
        API calls.
        """
        if not url_size in ['S', 'M']:
            raise ValueError("(url_size) must be 'S' or 'M'")

        new_url = thumb_url.split('/')

        if not 'Th.' == new_url[-1][-6:-3]:
            raise ValueError('(thumb_url) is not a thumbnail -> ' + thumb_url)

        file_ext = new_url[-1][-3:]
        new_url[-2] = url_size
        file_name = new_url[-1][:-6] + url_size
        file_name = file_name + '.' + file_ext
        new_url[-1] = file_name
        return '/'.join(new_url)

    def download_sample_image(self, image_url, image_path, new_name, retries=3):
        """
        Download a sample image. Sample images are smaller versions of full size 
        images. I typically seek the medium size and fall back to small or thumb if
        medium is not available. Medium is large enough to include in documents
        and contains enough pixels to determine dominant image color and tone.

            image_path = 'C:\\SmugMirror\\Mirror\\Places\Overseas\\BeirutLebanon1960s\\'
            image_url = 'https://photos.smugmug.com/Places/Overseas-Places/Beirut-Lebanon-1960s-1/i-nWGfNVx/1/88011d7e/Th/me%20on%20ship%20to%20egypt-Th.jpg'
            new_name = 'test-new-name.jpg'
            smug = SmugPyter()
            image_url = smug.larger_from_thumb_url(image_url)
            smug.download_sample_image(image_url, image_path, new_name) 
        """

        count = retries
        image_path_temp = image_path + "_temp"
        while count > 0:
            count -= 1

            # Doing the actual downloading
            self.show_yammer('downloading -> ' + new_name)
            image_data = self.smugmug_session.request(
                url=image_url, method='GET', stream=True).raw
            image_data.decode_content = True
            with open(image_path_temp, 'wb') as f:
                shutil.copyfileobj(image_data, f)

            os.rename(image_path_temp, image_path + new_name)
            break

            # if count > 0:
            #     print("Retrying...")
            # else:
            #     raise Exception("Error: Too many retries.")
            #     # probably no medium or small size - try getting the thumb

    def download_album_sample_images(self, manifest_file):
        """
        Download sample images for images listed in (manifest_file).
        Result is a tuple (image_count, new_count).

            smug = SmugPyter()
            manifest = r'C:\SmugMirror\Mirror\Places\Overseas\BeirutLebanon1960s\manifest-BeirutLebanon1960s-QPZ5K7-1m.txt'
            smug.download_album_sample_images(manifest)
        """
        image_count, new_count = 0, 0
        image_path = self.image_path_from_file(manifest_file)
        with open(manifest_file, 'r') as f:
            reader = csv.DictReader(f, dialect='excel', delimiter='\t')
            for row in reader:
                image_count += 1
                new_name = self.image_file_name(
                    row['ImageKey'], row['FileName'])

                # if an image already exists skip downloading
                # force reprocessing by deleting images
                if os.path.isfile(image_path + new_name):
                    continue

                thumb_url = row['ThumbnailUrl']
                new_url = self.larger_from_thumb_url(thumb_url)
                #print(new_url, image_path, new_name )
                self.download_sample_image(new_url, image_path, new_name)
                new_count += 1

        return (image_count, new_count)

    def update_all_sample_images(self, root):
        """
        Scan all manifest files in local directories and download sample
        images listed in manifest files that are not already present.

            smug = SmugPyter()
            smug.update_all_sample_images(r'c:\SmugMirror\Mirror')
        """
        return self.scan_do_local_files(root, func_do=self.download_album_sample_images)

    def scan_do_local_files(self, root, *, func_do=None, pattern='manifest-',
                            alist_filter=['txt']):
        """
        Scan files matching pattern and extension in local 
        directories and apply function (func_do).
        """
        total_images, total_changes = 0, 0
        for r, d, f in os.walk(root):
            for file in f:
                image_count, change_count = 0, 0
                if file[-3:] in alist_filter and pattern in file:
                    file_name = os.path.join(root, r, file)
                    if func_do is not None:
                        # self.show_yammer(file_name)
                        image_count, change_count = func_do(file_name)
                total_images += image_count
                total_changes += change_count
        return (total_images, total_changes)

    def case_mask_encode(self, smug_key):
        """
        Encode the case mask as an integer.
        """
        n = 0
        for i, c in enumerate(smug_key[::-1]):
            if c.isupper():
                n += 2 ** i
        return self.base36encode(n)

    def case_mask_decode(self, smug_key, case_mask):
        """
        Restore letter case to (smug_key).
        """
        # drop '0b' binary prefix
        mask = bin(self.base36decode(case_mask))[2:]
        if len(mask) > len(smug_key):
            raise ValueError(
                '(smug_key) length does not match (case_mask) length')
        # pad mask with '0's if necessary
        if len(mask) < len(smug_key):
            mask = ((len(smug_key) - len(mask)) * '0') + mask
        letters = list(smug_key)
        for i, (c, m) in enumerate(zip(letters, mask)):
            if '1' == m:
                letters[i] = c.upper()
        return ''.join(letters)

    def album_id_from_file(self, filename):
        """
        Extracts the (album_id, name, mask) from file names. 
        Depends on file naming conventions.

            album_id_from_file('c:\SmugMirror\Places\Overseas\Ghana1970s\manifest-Ghana1970s-Kng6tg-w.txt')    
        """
        mask, album_id, name = filename.split('-')[::-1][:3]
        mask = mask.split('.')[0]
        return (self.case_mask_decode(album_id, mask), name, mask)

    def changes_filename(self, manifest_file):
        """
        Changes file name from manifest file name.
        """
        album_id, name, mask = self.album_id_from_file(manifest_file)
        path = os.path.dirname(manifest_file)
        changes_name = "changes-%s-%s-%s" % (name, album_id, mask)
        changes_file = path + "/" + changes_name + '.txt'
        return changes_file

    def change_image_keywords(self, image_id, keywords, row):
        """
        Issue API PATCH request to change SmugMug keywords.
        NIMP: does not follow conventions of other requests 
        """

        noimage = row["ImageKey"] is None or row["ImageKey"] == ""
        nofile = row["FileName"] is None or row["FileName"] == ""
        if noimage or nofile:
            raise ValueError("(ImageKey, FileName) missing in row data")

        self.show_yammer(row['FileName'] + ' -> ' + keywords)

        # collect all keyword change requests - assuming
        # image key is unique over all images of a SmugMug account
        image_key = row['ImageKey']
        self.all_keyword_changes[image_key] = row

        r = requests.patch(url=self.smugmug_api_base_url + '/image/' + image_id,
                           auth=self.auth,
                           data=json.dumps({"Keywords": keywords}),
                           headers={'Accept': 'application/json',
                                    'Content-Type': 'application/json'},
                           allow_redirects=False)
        if r.status_code != 301:
            # NIMP: need a better exception type
            raise ValueError("PATCH request to change keywords failed")

        return (True, image_id)

    def change_keywords(self, changes_file):
        """
        Change keywords for images in album changes file.

            smug = SmugPyter()
            smug.yammer = True
            smug.change_keywords(r'C:\SmugMirror\Mirror\Themes\Diaries\CellPhoningItIn\changes-CellPhoningItIn-PfCsJz-16.txt')
        """
        change_count = 0
        with open(changes_file, 'r') as f:
            reader = csv.DictReader(f, dialect='excel', delimiter='\t')
            for row in reader:
                nokey = row["ImageKey"] is None or row["ImageKey"] == ""
                nowords = row["Keywords"] is None or row["Keywords"] == ""
                if nokey or nowords:
                    raise ValueError(
                        "(ImageKey, Keywords) missing in -> " + changes_file)
                change_count += 1
                image_key = row['ImageKey']
                keywords = row['Keywords']
                self.change_image_keywords(image_key, keywords, row)
        return (0, change_count)

    def image_dict_from_csv(self, image_file):
        """
        Load manifest or changes TAB delimited CSV file
        as a single dictionary keyed on (ImageKey).

            smug = SmugPyter()
            smug.image_dict_from_csv(r'c:\SmugMirror\Mirror\Places\Overseas\Ghana1970s\manifest-Ghana1970s-Kng6tg-w.txt') 
        """
        image_dict = {}
        with open(image_file, 'r') as f:
            reader = csv.DictReader(f, dialect='excel', delimiter='\t')
            for row in reader:
                if row["ImageKey"] is None or row["ImageKey"] == "":
                    raise ValueError("(ImageKey) missing in -> " + image_file)
                image_key = row['ImageKey']
                image_dict[image_key] = row
        return image_dict

    def show_yammer(self, message):
        """ conditional yammer message """
        if self.yammer:
            print(message)

    def image_file_name(self, image_key, file_name):
        """ Image file name from CSV (FileName) """
        key = image_key.strip()
        key = key + '-' + self.case_mask_encode(key)
        name = file_name.strip()
        new_name = key + ' ' + name
        # replace blanks with hyphens - simplifies LaTeX inclusions
        new_name = new_name.replace(' ', '-')
        return new_name

    def update_keywords(self, new_keyword, keywords, *,
                        key_pattern=r"\d+(\.\d+)?[xz]\d+(\.\d+)?",
                        split_delimiter=';'):
        """
        Add a (new_keyword) that matches (key_pattern) to existing keywords 
        and standardize the format of any remaining keywords. Existing keywords
        that match (key_pattern) are removed insuring (new_word) is the
        only keyword matching (key_pattern). Result (boolean, string) tuple.
        """
        # basic argument check
        error_message = '(new_keyword), (keywords) must be nonempty strings'
        if not (isinstance(new_keyword, str) and isinstance(keywords, str)):
            raise TypeError(error_message)
        elif len(new_keyword.strip(' ')) == 0:
            raise ValueError(error_message)

        if len(keywords.strip(' ')) == 0:
            return (False, new_keyword)

        keywords = split_delimiter + keywords
        inkeys = [s.strip().lower()
                  for s in keywords.split(split_delimiter) if len(s) > 0]
        inkeys = sorted(list(set(inkeys)))
        if 0 == len(inkeys):
            return (False, new_keyword)

        outkeys = [new_keyword]
        for inword in inkeys:
            # remove extant matching keys
            if re.match(key_pattern, inword) is not None:
                continue
            else:
                outkeys.append(inword)

        # return standard unique sorted keys
        outkeys = sorted(list(set(outkeys)))
        outkeys = self.standard_keywords(split_delimiter.join(outkeys))
        return (set(outkeys) == set(inkeys), (split_delimiter+' ').join(outkeys))

    def reset_changes_file(self, manifest_file):
        """
        Empties all changes files.
        Result is a tuple (image_count, change_count).

            smug = SmugPyter()
            manifest_file = 'c:\SmugMirror\Mirror\Places\Overseas\Ghana1970s\manifest-Ghana1970s-Kng6tg-w.txt'
            smug.reset_changes_file(manifest_file)
        """
        changed_keywords = []
        changed_keywords.append({'ImageKey': None, 'AlbumKey': None,
                                 'FileName': None, 'Keywords': None})
        image_count, change_count = 0, 0
        changes_file = self.changes_filename(manifest_file)
        keys = changed_keywords[0].keys()
        with open(changes_file, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(
                output_file, keys, dialect='excel-tab')
            dict_writer.writeheader()
            image_count += 1
            change_count += 1
        return (image_count, change_count)

    def reset_all_changes_files(self, root):
        """
        Empties all changes files in local directories.

            smug = SmugPyter()
            smug.reset_all_changes_files(r'c:\SmugMirror\Mirror')
        """
        return self.scan_do_local_files(root, func_do=self.reset_changes_file)

    def write_keyword_changes(self, manifest_file, func_keywords):
        """
        Write TAB delimited file of changed keywords.
        Return album and keyword (image_count, change_count) tuple.

            smug = SmugPyter()
            ck = ColorKeys() 
            manifest_file = 'c:\SmugMirror\Mirror\Places\Overseas\Ghana1970s\manifest-Ghana1970s-Kng6tg-w.txt'
            smug.write_keyword_changes(manifest_file, ck.color_keywords)  
        """
        image_count, change_count, keyword_changes = func_keywords(
            manifest_file)
        changes_file = self.changes_filename(manifest_file)
        keys = keyword_changes[0].keys()
        with open(changes_file, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(
                output_file, keys, dialect='excel-tab')
            dict_writer.writeheader()
            # for no changes write header only
            if change_count > 0:
                dict_writer.writerows(keyword_changes)
        return(image_count, change_count)

    def write_all_keyword_changes(self):
        """
        Write TAB delimited file of all keyword change requests.
        This file makes it easier to apply manual changes when
        the finicky PATCH request fails to change the damn
        keywords on SmugMug. Oh for an API that would
        just work!

            smug = SmugPyter()
            smug.write_all_keyword_changes()  
        """
        change_count = len(self.all_keyword_changes)
        if change_count == 0:
            self.show_yammer('no keyword change requests')
            return change_count

        # convert to dict writer friendly list
        change_list = []
        for key in self.all_keyword_changes.keys():
            change_list.append(self.all_keyword_changes[key])

        keys = change_list[0].keys()
        with open(self.all_keyword_changes_file, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(
                output_file, keys, dialect='excel-tab')
            dict_writer.writeheader()
            if change_count > 0:
                dict_writer.writerows(change_list)
        return change_count

    def update_all_keyword_changes(self, root):
        """
        Scan all changes files in local directories
        and apply keyword changes.

            smug = SmugPyter()
            smug.update_all_keyword_changes('c:\SmugMirror\Mirror')
        """
        self.all_keyword_changes = {}
        cnts = self.scan_do_local_files(root, pattern='changes-',
                                        func_do=self.change_keywords)
        self.write_all_keyword_changes()
        return cnts

    def changed_database_galleries(self, days_before=0):
        """
        Get galleries that SmugMug marked as changed in the last (days_before) days.

          # all galleries in descending last touch order
          smug.recently_changed_galleries() 

          # galleries touched in last 150 days
          smug.recently_changed_galleries(smug.days_before)

        """

        # default 0 gets all galleries
        if days_before == 0:
            after_days = ''
        else:
            past_date = (datetime.now() +
                         timedelta(days=-days_before)).isoformat()
            after_days = "where LastChange > '" + past_date + "' "

        # changed galleries
        cn = sqlite3.connect(self.mirror_database)
        cursor = cn.cursor()
        all_rows = cursor.execute("select AlbumName, AlbumKey, max(LastUpdated, ImagesLastUpdated) as LastChange \
                          from Album  " + after_days + " order by LastChange desc")
        all_rows = cursor.fetchall()
        cn.close()

        return all_rows
    
    def changed_online_galleries(self, days_before=0):
        """
        Get online galleries SmugMug marked as changed in the last (day_before) days.
        """
        
        albums = self.get_albums()
        ainfos = [self.get_album_info(j) for j in [i['AlbumKey'] for i in albums]]
        
        # default is all galleries
        if days_before == 0:
            return ainfos
        
        from_date = datetime.now() + timedelta(days=-days_before)
        from_date = pytz.utc.localize(from_date)
        
        # retain albums that are marked changed 
        rinfos = []
        for i, ainfo in enumerate(ainfos):
            last_change = max(dateutil.parser.parse(ainfo['LastUpdated']), dateutil.parser.parse(ainfo['ImagesLastUpdated']))
            if from_date < last_change:
                rinfos.append(ainfo)
                
        return rinfos   

    @staticmethod
    def extract_alphanum(in_string):
        return "".join([ch for ch in in_string if ch in (ascii_letters + digits)])

    @staticmethod
    def purify_smugmug_text(in_string):
        """
        Convert SmugMug unicode strings to ascii equivalents making non-ascii
        characters visible as XML escapes. Also convert embedded control 
        character to blanks.
        """
        purify = re.sub(' +', ' ', in_string)
        purify = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', purify)
        return purify.encode('ascii', 'xmlcharrefreplace').decode('ascii')

    @staticmethod
    def decode(obj, encoding='utf-8'):
        if isinstance(obj, str):
            if not isinstance(obj, str):
                obj = str(obj, encoding)
        return obj

    @staticmethod
    def base36encode(number):
        """
        Encode positive integer as a base 36 string.
        """
        if not isinstance(number, int):
            raise TypeError('number must be an integer')
        if number < 0:
            raise ValueError('number must be positive')
        alphabet, base36 = ['0123456789abcdefghijklmnopqrstuvwxyz', '']
        while number:
            number, i = divmod(number, 36)
            base36 = alphabet[i] + base36
        return base36 or alphabet[0]

    @staticmethod
    def base36decode(number):
        """
        Decode base 36 string and return integer.
        """
        return int(number, 36)

    @staticmethod
    def standard_keywords(keywords, *, blank_fill='_',
                          split_delimiter=';',
                          substitutions=[('united_states', 'usa')]):
        """
        Return a list of keywords in standard form.

        Reduces multiple blanks to one, converts to lower case, and replaces
        any remaining blanks with (blank_fill). This insures keywords are contiguous
        lower case or hyphenated lower case character runs.

        Note: the odd choice of '_' for the blank fill is because hyphens appear
        to be stripped from keywords on SmugMug.

            smug = SmugPyter()
            smug.standard_keywords('go;ahead;test me;boo    hoo  ; you   are   so; 0x0; united   states')
        """
        # basic argument check
        error_message = '(keywords) must be a string'
        if not isinstance(keywords, str):
            raise TypeError(error_message)

        if len(keywords.strip(' ')) == 0:
            return []
        else:
            keys = ' '.join(keywords.split())
            keys = split_delimiter.join(
                [s.strip().lower() for s in keys.split(split_delimiter)])
            keys = ''.join(blank_fill if c == ' ' else c for c in keys)
            # replace some keywords with others
            for k, s in substitutions:
                keys = keys.replace(k, s)
            # return sorted list
            keylist = [s for s in keys.split(split_delimiter)]
            return sorted(keylist)

    @staticmethod
    def dualsort(a, b, *, reverse=False):
        """
        Sort lists (a) and (b) using (a) to grade (b).
        """
        temp = sorted(zip(a, b), key=lambda x: x[0], reverse=reverse)
        return list(map(list, zip(*temp)))

    @staticmethod
    def round_to(n, precision):
        correction = 0.5 if n >= 0 else -0.5
        return int(n/precision+correction) * precision

    @staticmethod
    def image_path_from_file(manifest_file):
        """  Extract path from fully qualified manifest file names """
        if '\\' in manifest_file and '/' in manifest_file:
            raise ValueError(
                "use either win or unix path delimiters - not both")
        delimiter = '\\' if '\\' in manifest_file else '/'
        image_path = manifest_file.split(delimiter)
        image_path[-1] = ''
        image_path = delimiter.join(image_path)
        return image_path

    @staticmethod
    def local_path_from_parents(parent_folders, root, username):
        """ parse ParentFolders and return local directory path """
        try:
            # NOTE: the SmugMug parent folders uses any custom
            # folder names when building the path - make sure
            # no delimiter characters '- /' are embedded in custom names
            path_list = ((parent_folders.replace('-', '')
                          ).replace('!parents', '')).split('/')
            local_path = path_list[path_list.index(username):]
            local_path[0] = root
            local_path.append('/')
            local_path = "/".join(local_path)
            return local_path.replace('//', '/')
        except:
            return ''

# if __name__ == '__main__':
#
#    smug = SmugPyter()
#    smug.yammer = True
#
#    # smug.change_keywords('C:\SmugMirror\Themes\Diaries\CellPhoningItIn\changes-CellPhoningItIn-PfCsJz-16.txt')
#
#    smug.update_all_keyword_changes(r'c:\SmugMirror\Mirror')
