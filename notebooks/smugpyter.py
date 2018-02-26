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
#import httplib2
import hashlib
#import urllib.request, urllib.parse, urllib.error
import time
import sys
import os
import json
import configparser
import re
import shutil
import csv

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
    yammer = False
    
    # cannot create SmugPyter objects if this file is missing
    smugmug_config = os.path.join(os.path.expanduser("~"), '.smugpyter.cfg')


    def __init__(self, verbose=False, yammer=False):
        """
        Constructor. 
        Loads the config file and initialises the smugmug service
        """
        self.verbose = verbose
        self.argument_default = 'images'
        self.local_directory = 'c:/SmugMirror/'
        self.yammer = yammer
        
        config_parser = configparser.RawConfigParser()
        config_parser.read(SmugPyter.smugmug_config)
        try:
            self.username = config_parser.get('SMUGMUG','username')
            self.consumer_key = config_parser.get('SMUGMUG','consumer_key')
            self.consumer_secret = config_parser.get('SMUGMUG','consumer_secret')
            self.access_token = config_parser.get('SMUGMUG','access_token')
            self.access_token_secret = config_parser.get('SMUGMUG','access_token_secret')
            self.local_directory = config_parser.get('SMUGMUG','local_directory')
            self.google_maps_key = config_parser.get('GOOGLEMAPS','google_maps_key')
        except:
            raise Exception("Config file is missing or corrupted. Run 'python smugpyter.py'")

        self.smugmug_service = OAuth1Service(
            name='smugmug',
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            request_token_url=self.smugmug_request_token_uri,
            access_token_url=self.smugmug_access_token_uri,
            authorize_url=self.smugmug_authorize_uri)
        
        # NIMP: we don't need two authorizations - clean up 
        self.auth = requests_oauthlib.OAuth1(self.consumer_key, self.consumer_secret, self.access_token, 
                           self.access_token_secret, self.username)
            
        self.request_token, self.request_token_secret = self.smugmug_service.get_request_token(method='GET', params={'oauth_callback':'oob'})
        self.smugmug_session = self.smugmug_service.get_session((self.access_token, self.access_token_secret))
    
    
    def get_authorize_url(self):
        """
        Returns the URL for OAuth authorisation.
        """
        self.request_token, self.request_token_secret = self.smugmug_service.get_request_token(method='GET', 
                                                                                               params={'oauth_callback':'oob'})
        authorize_url = self.smugmug_service.get_authorize_url(self.request_token, Access='Full', Permissions='Add')
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
            print('\nREQUEST:\nmethod='+method+'\nurl='+url+'\nparams='+str(params)+'\nheaders='+str(headers))
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
            print('RESPONSE DATA:\n' + str(response.content)[:100] + (" ... " + str(response.content)[-100:] if len(str(response.content)) > 200 else ""))
        try:
            data = json.loads(response.content)
        except Exception:
            pass
        return data


    def request(self, method, url, params={}, headers={}, files={}, data=None, header_auth=False, retries=5, sleep=5):
        """
        Performs requests, with multiple attempts if needed.
        """
        retry_count=retries
        while retry_count > 0:
            try:
                response = self.request_once(method, url, params, headers, files, data, header_auth)
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
                albums.append({"Title": album['Title'], "Uri": album["Uri"], "AlbumKey": album["AlbumKey"]})

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
        
            smugmug = SmugPyter()
            smugmug.get_album_images('gLd4hT', "geomedia")
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
        images = sorted(images, key = lambda k: k["FileName"])
        return images


    def get_album_image_names(self, album_images): 
        """
        Get a list of {ImageKey, FileName} dictionaries for (album_images).
        
            smugmug = SmugPyter()
            album_images = smugmug.get_album_images('XghWcL')
            smugmug.get_album_image_names(album_images)
        """
        image_names = [{"ImageKey": i["ImageKey"], "FileName": i["FileName"]} for i in album_images]
        return image_names
  
     
    def get_album_image_captions(self, album_images):
        """
        Get a list of {ImageKey, Caption} dictionaries for (album_images).
        """
        image_captions = [{"ImageKey": i["ImageKey"], "Caption": i["Caption"]} for i in album_images]
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
                if self.yammer:
                    print('getting real date -> ' + imfile)
                response = self.request('GET', self.smugmug_api_base_url + "/image/" + key + "!metadata", 
                                        params=params, headers=headers)
                image_date = self.get_image_date(response['Response']['ImageMetadata'])
                
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
   
    
#    def create_album(self, album_name, password = None, folder_id = None, template_id = None):
#        """
#        Create a new album.
#        """
#        data = {"Title": album_name, "NiceName": self.create_nice_name(album_name), 
#                'OriginalSizes' : 1, 'Filenames' : 1}
#        if password != None:
#            data['Password'] = password
#
#        if template_id != None:
#            data["AlbumTemplateUri"] = template_id
#            data["FolderUri"] = "/api/v2/folder/user/"+self.username+("/"+folder_id if folder_id != None else "")+"!albums"
#            response = self.request('POST', 
#                                    self.smugmug_api_base_url + "/folder/user/"+self.username+("/"+folder_id if folder_id != None else "")+"!albumfromalbumtemplate", 
#                                    data=json.dumps(data), headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
#        else:
#            response = self.request('POST', 
#                                    self.smugmug_api_base_url + "/folder/user/"+self.username + ("/"+folder_id if folder_id != None else "") + "!albums", 
#                                    data=json.dumps(data), 
#                                    headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
#
#        if self.verbose == True:
#            print(json.dumps(response))
#
#        return response


    def get_album_info(self, album_id):
        """
        Get info for an album.
            
            smug = SmugPyter()
            smug.get_album_info('QPZ5K7')
        """
        if self.verbose == True:
            print("Getting albums")
            
        response = self.request('GET', self.smugmug_api_base_url + "/album/"+album_id, 
                                headers={'Accept': 'application/json'})
        return response["Response"]["Album"]

        album_info = dict()
        album_key = self.get_album_key(album_id)
        response = self.request('GET', self.smugmug_api_uri, params={'method':'smugmug.albums.getInfo', 
                                                                     'AlbumID':album_id, 'AlbumKey':album_key})
        album_info['album_id'] = response['Album']['id']
        album_info['album_name'] = response['Album']['Title']
        album_info['category_id'] = response['Album']['Category']['id']
        album_info['category_name'] = response['Album']['Category']['Name']
        return album_info

    
    def get_child_node_uri(self, node_id):
        """
        Get child node uri.
        """ 
        response = self.request('GET', self.smugmug_api_base_url + "/node/" + node_id, 
                                 headers={'Accept': 'application/json'})
        uri = response["Response"]["Node"]["Uris"]["ChildNodes"]["Uri"]
        return uri
  
      
    def mirror_folders_offline(self, root_uri, root_dir, func_album=None, func_folder=None):
        """
        Recursively walk online SmugMug folders and albums and apply
        functions (func_album) and (func_folder).
        """
        root_uri = (self.smugmug_base_uri + '%s') % root_uri
        if not '!children' in root_uri:
            root_uri += '!children'
        #print('url = ' + root_uri)
        response = self.request('GET', root_uri, headers={'Accept': 'application/json'})
        for node in response["Response"]["Node"]:
            name = self.extract_alphanum(node["Name"])
            path = '%s/%s' % (root_dir, name)
            #print(path)
            os.makedirs(path, exist_ok=True)
            if node["Type"] == 'Folder':
                if not func_folder == None:
                    func_folder(name, path)
                self.mirror_folders_offline(node["Uri"], path, func_album)
            elif node['Type'] == 'Album':
                print('visiting album ' + name)
                uri = node["Uris"]["Album"]["Uri"]
                album_id = uri.split('/')[-1]
                if not func_album == None:
                    func_album(album_id, name, path)
            
                #Queue for download
                #master_albums_list.append(path)
                #dl_queue.put({'node' : node, 'path' : path})
        
        #if 'NextPage' in response['Response']['Pages']:
        #    self.mirror_folders_offline(pages['NextPage'], root_dir)
  
      
    def download_smugmug_mirror(self, func_album=None, func_folder=None):
        """
        Walk SmugMug folders and albums and apply functions (func_album) and (func_folder).
        
            smug = SmugPyter()
            smug.download_smugmug_mirror(func_album=smug.write_album_manifest) 
        """
        root_folder = self.local_directory
        folders = self.get_folders()
        for folder in folders:
            root_uri = self.get_child_node_uri(folder["NodeID"])
            top_folder = self.extract_alphanum(folder["Name"])
            self.mirror_folders_offline(root_uri, root_folder + top_folder, 
                                        func_album, func_folder)
        print("done")
 
                    
    def write_album_manifest(self, album_id, name, path):
        """
        Write TAB delimited file of SmugMug image metadata.
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
            dict_writer = csv.DictWriter(output_file, keys, dialect='excel-tab')
            dict_writer.writeheader()
            dict_writer.writerows(album_images)
  
          
    def write_album_real_dates(self, album_id, name, path):
        """
        Write TAB delimited file of SmugMug image real dates.
        
        My image dates vary from fairly reliable EXIF dates
        to wild guesses about century old prints. SmugMug 
        requires a full date and it looks in a number
        of places for full dates, see: (get_image_date).
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
       
        real_dates = self.get_album_image_real_dates(album_images, realdate_dict=realdate_dict)
        if len(real_dates) == 0:
            return None
        
        keys = real_dates[0].keys()
        with open(realdate_file, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys, dialect='excel-tab')
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
        
            image_path = 'C:\\SmugMirror\\Places\Overseas\\BeirutLebanon1960s\\'
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
            print('downloading -> ' + new_name)
            image_data = self.smugmug_session.request(url=image_url, method='GET', stream=True).raw
            image_data.decode_content = True
            with open(image_path_temp, 'wb') as f:
                shutil.copyfileobj(image_data, f)
            
            # WARNING: extensions may not be (jpg)
            os.rename(image_path_temp, image_path + new_name)
            break

            if count > 0:
                print("Retrying...")
            else:
                raise Exception("Error: Too many retries.")
                #probably no medium or small size - try getting the thumb
                
    
    def download_album_sample_images(self, manifest_file):
        """
        Download sample images for images listed in (manifest_file).
        Result is a tuple (image_count, new_count).
        
            smug = SmugPyter()
            manifest = 'C:\SmugMirror\Places\Overseas\BeirutLebanon1960s\manifest-BeirutLebanon1960s-QPZ5K7-1m.txt'
            smug.download_album_sample_images(manifest)
        """
        image_count , new_count = 0 , 0
        # drop file name
        image_path = manifest_file.split('\\')
        image_path[-1] = ''
        image_path = '\\'.join(image_path) + '\\'
        #print(image_path)
        with open(manifest_file, 'r') as f:
            reader = csv.DictReader(f, dialect='excel', delimiter='\t')                     
            for row in reader:
                image_count += 1
                key = row['ImageKey'].strip()
                key = key + '-' + self.case_mask_encode(key)
                file_name = row['FileName'].strip()
                new_name = key + ' ' + file_name
                # replace blanks with hyphens - simplifies LaTeX inclusions
                new_name = new_name.replace(' ', '-')
                thumb_url = row['ThumbnailUrl']
                new_url = self.larger_from_thumb_url(thumb_url)
                #print(new_url, image_path, new_name )
                self.download_sample_image(new_url, image_path, new_name)
                
        return (image_count, new_count)
    
        
#    def download_image(self, image_info, image_path, retries=5):
#        """
#        Download an image from a url.
#        """
#        count = retries
#        image_url = self.get_image_download_url(image_info["ImageKey"])
#        image_path_temp = image_path + "_temp"
#
#        while count > 0:
#            count -= 1
#            # Doing the actual downloading
#            image_data = self.smugmug_session.request(url=image_url, method='GET', stream=True).raw
#            image_data.decode_content = True
#            with open(image_path_temp, 'wb') as f:
#                shutil.copyfileobj(image_data, f)
#            
#            # Checking the image
#            image_data_local = self.load_image(image_path_temp)
#            image_md5sum = hashlib.md5(image_data_local).hexdigest()
#            image_size = str(len(image_data_local))
#            if image_md5sum != image_info['ArchivedMD5']:
#                raise Exception("MD5 sum doesn't match.")
#            elif image_size != str(image_info['OriginalSize']):
#                raise Exception("Image size doesn't match.")
#            else:
#                os.rename(image_path_temp, image_path)
#                break
#
#            if count > 0:
#                print("Retrying...")
#            else:
#                raise Exception("Error: Too many retries.")
#                sys.exit(1)
                
                
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
            raise ValueError('(smug_key) length does not match (case_mask) length')
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
    
    
    def change_image_keywords(self, image_id, keywords):
        """
        Issue API PATCH request to change SmugMug keywords.
        NIMP: does not follow conventions of other requests 
        """
        r = requests.patch(url=self.smugmug_api_base_url + '/image/' + image_id,
                           auth=self.auth,
                           data=json.dumps({"Keywords": keywords}),
                           headers={'Accept':'application/json','Content-Type':'application/json'},
                           allow_redirects=False)
        if r.status_code != 301:
            # NIMP: need a better exception type
            raise ValueError("PATCH request to change keywords failed")

        return (True, image_id)
    
    
    def change_keywords(self, changes_file):
        """
        Change keywords for images in album changes file.
        """
        change_count = 0
        with open(changes_file, 'r') as f:
            reader = csv.DictReader(f, dialect='excel', delimiter='\t')
            # NIMP: check that required columns are present                   
            for row in reader:
                change_count += 1
                image_key = row['ImageKey']
                keywords = row['Keywords']
                #print(key, keywords)
                self.change_image_keywords(image_key, keywords)
        return change_count
    
    
    def image_dict_from_csv(self, image_file):
        """
        Load manifest or changes TAB delimited CSV file
        as a single dictionary keyed on (ImageKey).
        
            smug = SmugPyter()
            smug.image_dict_from_csv('c:\SmugMirror\Places\Overseas\Ghana1970s\manifest-Ghana1970s-Kng6tg-w.txt') 
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
        

    @staticmethod
    def load_image(image_path):
        """
        Load the image data from a path.
        """
        try:
            image_data = open(image_path, 'rb').read()
            return image_data
        except IOError as e:
            raise "I/O error({0}): {1}".format(e.errno, e.strerror)
        return None
   
    
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
        return purify.encode('ascii', 'xmlcharrefreplace' ).decode('ascii')
   
    
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
                      substitutions=[('united_states','usa')]):
        """
        Return a list of keywords in standard form.
        
        Reduces multiple blanks to one, converts to lower case, and replaces
        any remaining blanks with (blank_fill). This insures keywords are contigous
        lower case or hypenated lower case character runs.
        
        Note: the odd choice of '_' for the blank fill is because hyphens appear
        to be stripped from keywords on SmugMug.
        
            standard_keywords('go;ahead;test me;boo    hoo  ; you   are   so; 0x0; united   states')
        """
        # basic argument check
        error_message = '(keywords) must be a string'
        if not isinstance(keywords, str):
            raise TypeError(error_message)
        
        if len(keywords.strip(' ')) == 0:
            return []
        else:
            keys = ' '.join(keywords.split())                         
            keys = split_delimiter.join([s.strip().lower() for s in keys.split(split_delimiter)])
            keys = ''.join(blank_fill if c == ' ' else c for c in keys)
            # replace some keywords with others
            for k, s in substitutions:
                keys = keys.replace(k, s)
            # return sorted list - move size keys to front     
            keylist = [s for s in keys.split(split_delimiter)]
            return sorted(keylist)
    
    
    @staticmethod
    def dualsort(a, b):
        """
        Sort lists (a) and (b) using (a) to grade (b).
        """
        temp = sorted(zip(a, b), key=lambda x: x[0])
        return list(map(list, zip(*temp)))
    
    
    @staticmethod
    def round_to(n, precision):
        correction = 0.5 if n >= 0 else -0.5
        return int( n/precision+correction ) * precision